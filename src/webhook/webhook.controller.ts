import { Body, Controller, Post } from '@nestjs/common';
import { WebhookService } from './webhook.service';

@Controller('webhook')
export class WebhookController {
  constructor(private webhookService: WebhookService) {}

  @Post()
  async handleGitHubWebhook(@Body() payload: any) {
    if (payload.action == 'opened' && payload.pull_request) {
      await this.webhookService.handlePullRequest(payload);
      return {success: true};
    }
    return {success: false};
  }
}
