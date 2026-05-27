import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { WebhookModule } from './webhook/webhook.module';
import { RedisModule } from './redis.module';
import { ReviewModule } from './review/review.module';
import { GithubService } from './github/github.service';
import { GithubModule } from './github/github.module';

@Module({
  imports: [WebhookModule, RedisModule, ReviewModule, GithubModule],
  controllers: [AppController],
  providers: [AppService, GithubService],
})
export class AppModule {}
