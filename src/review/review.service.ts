import { Injectable, OnModuleDestroy, OnModuleInit } from '@nestjs/common';
import OpenAI from 'openai';
import { RedisService } from 'src/redis.service';

@Injectable()
export class ReviewService implements OnModuleInit, OnModuleDestroy {
  constructor(private redisService: RedisService) {}

  async onModuleInit() {
    console.log(
      'Review Service starting - subscribing to pull-request channel',
    );
    try {
      await this.redisService.subscribe('pull-request', (message: string) => {
        this.processPullRequest(JSON.parse(message)).catch((err) =>
          console.error('Error processing PR:', err),
        );
      });
    } catch (err) {
      console.error('Failed to publish review to Redis', err);
    }
  }

  async onModuleDestroy() {
    console.log('Review service shutting down');
  }

  private async processPullRequest(prData: any) {
    console.log(`Processing PR ${prData.prNumber}: ${prData.title}`);

    try {
      const review = await this.reviewWithDeepSeek(prData);
      await this.redisService.publish('reviews', JSON.stringify(review));

      console.log(
        `Review for PR #${prData.prNumber} published to reviews channel`,
      );
    } catch (err) {
      console.error('Failed to publish review to Redis', err);
    }
  }

  private async reviewWithDeepSeek(prData: any) {
    try {
      if (!process.env.DEEPSEEK_API_KEY) {
        throw new Error('DEEPSEEK_API_KEY not set in the environment');
      }
      const client = new OpenAI({
        apiKey: process.env.DEEPSEEK_API_KEY,
        baseURL: 'https://api.deepseek.com/v1',
      });

      const prompt = `
        You are a code reviewer. Review this pull request:

        Title: ${prData.title}
        Description: ${prData.body || 'No description provided'}

        Provide a concise review with:
        1. Key observations
        2. Suggestions for improvement
        3. Approval status  (Approved/Request Changes)
      `;

      const message = await client.chat.completions.create({
        model: 'deepseek-chat',
        max_tokens: 1024,
        messages: [
          {
            role: 'user',
            content: prompt,
          },
        ],
      });

      const reviewText = message.choices[0].message.content || '';

      return {
        prNumber: prData.prNumber,
        review: reviewText,
        repository: prData.repository,
      };
    } catch (error) {
      console.error('DeepSeek API error:', error);
      return {
        prNumber: prData.prNumber,
        review: 'X Review Failed. Please try again',
        repository: prData.repository,
      };
    }
  }
}
