const redis = require('redis');

console.log(process.env.REDIS_HOST);

const redisHost = process.env.REDIS_HOST || 'redis'; // docker-compose service name
const redisPort = process.env.REDIS_PORT || 6379;

const redisUrl = `redis://${redisHost}:${redisPort}}`;

const client = redis.createClient({
  url: redisUrl,
  retry_strategy: () => 1000, // try reconnecting after 1 sec
});

client.on('error', (err) => {
  console.log('error', err, process.env.REDIS_HOST, process.env.REDIS_PORT);
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
