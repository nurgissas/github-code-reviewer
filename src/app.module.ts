import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { WebhookModule } from './webhook/webhook.module';
import { RedisModule } from './redis.module';
import { GithubService } from './github/github.service';
import { GithubModule } from './github/github.module';

// NOTE: The NestJS ReviewModule (single DeepSeek call) has been replaced by the
// Python LangGraph agent service, which subscribes to the same "pull-request"
// channel. Registering both would post two comments per PR, so ReviewModule is
// intentionally left out of the imports below.

@Module({
  imports: [WebhookModule, RedisModule, GithubModule],
  controllers: [AppController],
  providers: [AppService, GithubService],
})
export class AppModule {}
