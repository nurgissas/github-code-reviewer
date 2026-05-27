import { Injectable, OnModuleDestroy, OnModuleInit } from '@nestjs/common';
import { RedisService } from 'src/redis.service';

@Injectable()
export class GithubService implements OnModuleInit, OnModuleDestroy {
  private githubToken = process.env.GITHUB_TOKEN;

  constructor(private redisService: RedisService) {}

  async onModuleInit() {
    if (!this.githubToken) {
      throw new Error('GITHUB_TOKEN not set in the env');
    }
    console.log('Github Service starting - subscribing to reviews channel');

    await this.redisService.subscribe('reviews', (message: string) => {
      this.postReviewToGithub(JSON.parse(message)).catch((err) =>
        console.error('Error posting reviews to Github:', err),
      );
    });
  }

  async onModuleDestroy() {
    console.log('Github Service shutting down');
  }

  private async postReviewToGithub(reviewData: any) {
    if (!reviewData.prNumber || !reviewData.repository || !reviewData.review) {
      throw new Error('Invalid review data - missing required fields');
    }
    console.log(
      `Posting review to PR #${reviewData.prNumber} to ${reviewData.repository}`,
    );

    const [owner, repo] = reviewData.repository.split('/');

    const url = `https://api.github.com/repos/${owner}/${repo}/issues/${reviewData.prNumber}/comments`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `token ${this.githubToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          body: reviewData.review,
        }),
      });

      if (!response.ok) {
        throw new Error(`Github API error: ${response.statusText}`);
      }
      console.log(`Review posted successfully to PR #${reviewData.prNumber}`);
    } catch (err) {
      console.error('Failed to post review to Github:', err);
      throw err;
    }
  }
}
