import { Injectable, OnModuleDestroy, OnModuleInit } from '@nestjs/common';
import { RedisService } from 'src/redis.service';

@Injectable()
export class GithubService implements OnModuleInit, OnModuleDestroy {
  private githubToken = process.env.GITHUB_TOKEN;

  constructor(private redisService: RedisService) {}
}
