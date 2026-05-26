import { Module } from '@nestjs/common';
import { ReviewService } from './review.service';
import { RedisModule } from 'src/redis.module';

@Module({
  imports: [RedisModule],
  providers: [ReviewService],
})
export class ReviewModule {}
