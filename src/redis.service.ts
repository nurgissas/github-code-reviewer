import { Injectable, OnModuleDestroy, OnModuleInit } from '@nestjs/common';
import { createClient } from 'redis';

@Injectable()
export class RedisService implements OnModuleInit, OnModuleDestroy {
  private client = createClient({
    url: process.env.REDIS_URL || 'redis://localhost:6379',
    password: process.env.REDIS_PASSWORD,
  });

  async onModuleInit() {
    try {
      await this.client.connect();
      console.log('Redis connected');
    } catch (err) {
      console.error('Failed to connect to Redis:', err);
      console.error('Retrying in 2 seconds...');
      setTimeout(() => this.onModuleInit(), 2000);
    }
  }

  async onModuleDestroy() {
    await this.client.quit();
  }

  async publish(channel: string, message: string) {
    await this.client.publish(channel, message);
  }

  async subscribe(channel: string, callback: (message: string) => void) {
    const subscriber = this.client.duplicate();
    await subscriber.connect();
    await subscriber.subscribe(channel, callback);
  }
}
