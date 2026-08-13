import { Injectable } from '@nestjs/common';
import { RedisService } from 'src/redis.service';

@Injectable()
export class WebhookService {
  constructor(private redisService: RedisService) {}

  async handlePullRequest(payload: any) {
    if (!payload.pull_request || !payload.repository || !payload.number) {
      throw new Error(
        'Invalid Github webhook payload - missing required fields',
      );
    }

    try {
      const message = JSON.stringify({
        action: payload.action,
        prNumber: payload.number ?? payload.pull_request.number,
        // Full "owner/repo" — the GitHub service splits this to post the comment.
        repository: payload.repository.full_name,
        owner: payload.repository.owner?.login,
        repo: payload.repository.name,
        title: payload.pull_request.title,
        body: payload.pull_request.body,
      });
      await this.redisService.publish('pull-request', message);
    } catch (err) {
      console.error('Error handling PR webhook:', err);
      throw err;
    }
  }
}
