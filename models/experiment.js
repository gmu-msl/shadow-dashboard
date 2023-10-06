// We're using redis to store the dashboard data.
// This is because we don't plan to store the data in the database yet.
const redisClient = require('../utils/redis');

const { REDIS_DASHBOARD_EXPERIMENTS_SET } = require('../utils/constants');

class experimentObject {
  constructor({
    experimentName,
    config,
    originalname,
    filename,
    path,
    unzippedFolderName,
    createdAt,
    completedAt,
    pickleFile,
    status,
    currentFunction,
    logListKey,
    jobsTopic,
    jobsCreated,
  }) {
    this.experimentName = experimentName;
    this.config = config;
    this.originalname = originalname;
    this.filename = filename;
    this.path = path;
    this.unzippedFolderName = unzippedFolderName;
    this.createdAt = createdAt;
    this.completedAt = completedAt;
    this.pickleFile = pickleFile;
    this.status = status;
    this.currentFunction = currentFunction;
    this.logListKey = logListKey;
    this.jobsTopic = jobsTopic;
    this.jobsCreated = jobsCreated;
  }
}

const checkAndReturnExistingExperiment = async (experimentName) => {
  try {
    const experimentHash = await redisClient.hGetAll(
      `${REDIS_DASHBOARD_EXPERIMENTS_SET}:${experimentName}`
    );
    return experimentHash;
  } catch (error) {
    throw error;
  }
};

const addExperimentToDashboard = async (experimentHash) => {
  try {
    // Add experiment to a hash using hset
    // Add the redis key to a set using sadd
    const { experimentName } = experimentHash;

    // To ensure atomicity, use a transaction
    const multi = redisClient.multi();

    multi.hSet(
      `${REDIS_DASHBOARD_EXPERIMENTS_SET}:${experimentName}`,
      experimentHash
    );
    multi.sAdd(REDIS_DASHBOARD_EXPERIMENTS_SET, experimentName);

    const result = await multi.exec();
    return result;
  } catch (error) {
    throw error;
  }
};

const updateExperimentInDashboard = async (experimentName, update) => {
  try {
    // check if experiment exists
    const experimentHash = await checkAndReturnExistingExperiment(
      experimentName
    );

    if (experimentHash && Object.keys(experimentHash).length === 0) {
      throw new Error('Experiment does not exist');
    }

    // update the experiment
    const result = await redisClient.hSet(
      `${REDIS_DASHBOARD_EXPERIMENTS_SET}:${experimentName}`,
      update
    );

    return result;
  } catch (error) {
    throw error;
  }
};

const getExperimentsForDashboard = async () => {
  try {
    // Get all experiments from the set
    const experiments = await redisClient.sMembers(
      REDIS_DASHBOARD_EXPERIMENTS_SET
    );

    // Get all the experiments from the hash
    const multi = redisClient.multi();

    experiments.forEach((experiment) => {
      multi.hGetAll(`${REDIS_DASHBOARD_EXPERIMENTS_SET}:${experiment}`);
    });

    const result = await multi.exec();

    return result;
  } catch (error) {
    throw error;
  }
};

const addLogToLogList = async (logListKey, log) => {
  try {
    const result = await redisClient.lPush(logListKey, JSON.stringify(log));
    return result;
  } catch (error) {
    throw error;
  }
};

const updateJobsCreatedForExperimentByChekingListInRedis = async (
  experimentName,
  jobsList
) => {
  try {
    const countOfJobsCreated = await redisClient.lLen(jobsList);
    await updateExperimentInDashboard(experimentName, {
      jobsCreated: countOfJobsCreated,
    });
  } catch (error) {
    throw error;
  }
};

const publishMessageToJobsTopic = async (topic, message) => {
  try {
    const result = await redisClient.publish(topic, message);
    return result;
  } catch (error) {
    throw error;
  }
};

const getExperimentForViewExperiment = async (experimentName) => {
  try {
    const experimentHash = await redisClient.hGetAll(
      `${REDIS_DASHBOARD_EXPERIMENTS_SET}:${experimentName}`
    );

    // check if experiment exists
    if (experimentHash && Object.keys(experimentHash).length === 0) {
      throw new Error('Experiment does not exist');
    }

    // for the experiment, get the log list
    const logListKey = experimentHash.logListKey;
    let logList = await redisClient.lRange(logListKey, 0, -1);

    // reverse the log list so that the order is preserved
    logList = logList.reverse();

    const experiment = {
      ...experimentHash,
      logList,
    };

    return experiment;
  } catch (error) {
    throw error;
  }
};

module.exports = {
  experimentObject,
  checkAndReturnExistingExperiment,
  addExperimentToDashboard,
  updateExperimentInDashboard,
  getExperimentsForDashboard,
  addLogToLogList,
  updateJobsCreatedForExperimentByChekingListInRedis,
  publishMessageToJobsTopic,
  getExperimentForViewExperiment,
};
