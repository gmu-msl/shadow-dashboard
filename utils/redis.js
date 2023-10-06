const redis = require('redis');

const { REDIS_HOST, REDIS_PORT } = require('./constants');

const redisUrl = `redis://${REDIS_HOST}:${REDIS_PORT}`;

const client = redis.createClient({
  url: redisUrl,
  retry_strategy: () => 1000, // try reconnecting after 1 sec
});

client.on('error', (err) => {
  console.log('error', err, REDIS_HOST, REDIS_PORT);
});

client.on('connect', () => {
  console.log('Redis client connected');
});

client.on('ready', () => {
  console.log('Redis client ready to use');
});

client.on('end', () => {
  console.log('Redis client disconnected');
});

// connect to redis
client.connect();

module.exports = client;
