import { Module } from '@nestjs/common';
import { WebhookController } from './webhook.controller';
import { WebhookService } from './webhook.service';
import { RedisModule } from 'src/redis.module';

@Module({
  imports: [RedisModule],
  controllers: [WebhookController],
  providers: [WebhookService],
})
export class WebhookModule {}
