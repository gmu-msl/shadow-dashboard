// Add all constants here
const REDIS_DASHBOARD_EXPERIMENTS_SET = 'REDIS_DASHBOARD_EXPERIMENTS_SET';

const MONGOHOST = process.env.MONGO_HOST || 'localhost';
const MONGOPORT = process.env.MONGO_PORT || 27017;
const REDIS_HOST = process.env.REDIS_HOST || 'localhost'; // docker-compose service name
const REDIS_PORT = process.env.REDIS_PORT || 6379;
const SHARED_FOLDER = process.env.SHARED_FOLDER || './evaluators'; // by default use the current folder

const POST_PROCESSOR_PATH = './processors/postprocess-python';
const PRE_PROCESSOR_PATH = './processors/preprocess-python';

const REDIS_JOB_NOTIFY_CHANNEL = 'REDIS_JOB_NOTIFY_CHANNEL';

module.exports = {
  REDIS_DASHBOARD_EXPERIMENTS_SET,
  REDIS_HOST,
  REDIS_PORT,
  SHARED_FOLDER,
  POST_PROCESSOR_PATH,
  PRE_PROCESSOR_PATH,
  REDIS_JOB_NOTIFY_CHANNEL,
  MONGOHOST,
  MONGOPORT,
};
