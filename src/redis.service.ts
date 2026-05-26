import { Injectable, OnModuleDestroy, OnModuleInit } from '@nestjs/common';
import { createClient } from 'redis';

@Injectable()
export class RedisService implements OnModuleInit, OnModuleDestroy{
  private client = createClient({
    url: 'redis://localhost:6379',
  });

  async onModuleInit(){
    await this.client.connect();
    console.log('Redis connected');
  }

  async onModuleDestroy(){
    await this.client.quit();
  }

  async publish(channel: string, message: string) {
    await this.client.publish(channel, message);
  }

  async subscribe(channel: string, callback: (message: string) => void){
    const subscriber = this.client.duplicate();
    await subscriber.connect();
    await subscriber.subscribe(channel, callback);
  }
}
