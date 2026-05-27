import { Module } from '@nestjs/common';
import { RedisModule } from 'src/redis.module';

@Module({
  imports: [RedisModule],
})
export class GithubModule {}
