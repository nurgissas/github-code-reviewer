import { Injectable } from '@nestjs/common';
import { RedisService } from 'src/redis.service';

@Injectable()
export class WebhookService {
  constructor(private redisService: RedisService) {}

  async handlePullRequest(payload: any) {
    const message = JSON.stringify({
      action: payload.action,
      prNumber: payload.number,
      repository: payload.repository.name,
      title: payload.pull_request.title,
      body: payload.pull_request.body,
    });
    await this.redisService.publish('pull-request', message);
  }
}
