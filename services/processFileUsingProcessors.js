// This is a service file that will be used by the controller to process the file.
const fs = require('fs');
const util = require('util');
const exec = util.promisify(require('child_process').exec);
const crypto = require('crypto');

const {
  REDIS_HOST,
  SHARED_FOLDER,
  PRE_PROCESSOR_PATH,
  REDIS_JOB_NOTIFY_CHANNEL,
} = require('../utils/constants');

const {
  updateExperimentInDashboard,
  addLogToLogList,
  updateJobsCreatedForExperimentByChekingListInRedis,
  publishMessageToJobsTopic,
} = require('../models/experiment');

const processUsingPythonProcessor = async ({
  originalFileName,
  path,
  experimentName,
  config,
  unzippedFolderName,
  pickleFileName,
  redisTopicForJobs,
  logListKey,
  uploadedPickleFile,
}) => {
  try {
    // update the experiment to say processing
    await updateExperimentInDashboard(experimentName, {
      status: 'processing',
      currentFunction: 'unzip',
    });

    // 1. Move file to processor (tmp with the experiment name)
    const processorFilePath = `./processors/preprocess-python/${experimentName}`;

    if (!fs.existsSync(processorFilePath)) {
      fs.mkdirSync(processorFilePath, { recursive: true });
    }

    fs.copyFileSync(path, `${processorFilePath}/${originalFileName}`);

    // 2. unzip file
    const unzipCommand = !!uploadedPickleFile
      ? `gunzip -c ${processorFilePath}/${originalFileName} > ${processorFilePath}/${pickleFileName}`
      : `unzip ${processorFilePath}/${originalFileName} -d ${processorFilePath}`;
    const unzipCommandExec = await exec(unzipCommand);

    await addLogToLogList(logListKey, {
      stdout: unzipCommandExec.stdout,
      stderr: unzipCommandExec.stderr,
    });

    // 3. remove the zip file, we don't need it anymore
    fs.unlinkSync(`${processorFilePath}/${originalFileName}`);

    // 4. create csv folder and server_log folder in the unzipped folder
    // only do the following steps if the pickle file is not uploaded and we need to run the processor
    if (!!!uploadedPickleFile) {
      const csvFolder = `${processorFilePath}/${unzippedFolderName}/csv`;
      const serverLogFolder = `${processorFilePath}/${unzippedFolderName}/server_log`;
      if (!fs.existsSync(csvFolder)) {
        fs.mkdirSync(csvFolder, { recursive: true });
      }

      if (!fs.existsSync(serverLogFolder)) {
        fs.mkdirSync(serverLogFolder, { recursive: true });
      }

      await updateExperimentInDashboard(experimentName, {
        currentFunction: 'pcap_to_csv.sh',
      });

      // 5. Run pcap_to_csv.sh from inside the unzipped folder csv folder
      // also move the pythonServerThread.log to the server_log folder as pythonServerThread.stdout
      const pcapToCsvCommand = `cd ${csvFolder} && ../../../pcap_to_csv.sh ../`;
      const pcapToCsvCommandExec = await exec(pcapToCsvCommand);

      console.log('pcapToCsvCommandExec completed');
      await addLogToLogList(logListKey, {
        stdout: pcapToCsvCommandExec.stdout,
        stderr: pcapToCsvCommandExec.stderr,
      });

      // move the pythonServerThread.log to the server_log folder as pythonServerThread.stdout
      fs.renameSync(
        `${processorFilePath}/${unzippedFolderName}/pythonServerThread.log`,
        `${processorFilePath}/${unzippedFolderName}/server_log/pythonServerThread.stdout`
      );

      // 6. write the config yaml to the same tmp folder
      const configFilePath = `./${processorFilePath}/${unzippedFolderName}/config.yaml`;
      fs.writeFileSync(configFilePath, config);

      await updateExperimentInDashboard(experimentName, {
        currentFunction: 'loadFilesAndGeneratePickle.py',
      });

      // 7. run the processor with the above stuff as params
      const configFileParam = `./${experimentName}/${unzippedFolderName}/config.yaml`;
      const csvFolderParam = `./${experimentName}/${unzippedFolderName}/csv/`;
      const serverLogFolderParam = `./${experimentName}/${unzippedFolderName}/server_log/`;

      const processorCommand = `cd ${PRE_PROCESSOR_PATH} && /root/.local/bin/poetry run python3 loadFilesAndGeneratePickle.py ${configFileParam} ${pickleFileName} ${csvFolderParam} ${serverLogFolderParam}`;
      const processorCommandExec = await exec(processorCommand);

      console.log('processorCommandExec completed');

        let pickleFilePath = `${PRE_PROCESSOR_PATH}/${pickleFileName}`;

        const cpPickleFileCommand = `cp ${pickleFilePath} ${SHARED_FOLDER}`;
        const cpPickleFileCommandExec = await exec(cpPickleFileCommand);

        await addLogToLogList(logListKey, {
            stdout: cpPickleFileCommandExec.stdout,
            stderr: cpPickleFileCommandExec.stderr,
        });

      await addLogToLogList(logListKey, {
        stdout: processorCommandExec.stdout,
        stderr: processorCommandExec.stderr,
      });
    } else {
      // copy the pickle file to the processor folder
      fs.copyFileSync(
        `${processorFilePath}/${pickleFileName}`,
        `${PRE_PROCESSOR_PATH}/${pickleFileName}`
      );
    }

    await updateExperimentInDashboard(experimentName, {
      currentFunction: 'generateTasks.py',
      pickleFileName,
    });

    const generateTasksCommand = `cd ${PRE_PROCESSOR_PATH} && /root/.local/bin/poetry run python3 generateTasks.py ${experimentName} ${pickleFileName} ${REDIS_HOST} ${redisTopicForJobs}`;
    const generateTasksCommandExec = await exec(generateTasksCommand);

    console.log('generateTasksCommandExec completed');

    await addLogToLogList(logListKey, {
      stdout: generateTasksCommandExec.stdout,
      stderr: generateTasksCommandExec.stderr,
    });

    await updateJobsCreatedForExperimentByChekingListInRedis(
      experimentName,
      redisTopicForJobs
    );

    // move the pickle file to the shared folder
    let pickleFilePath = `${PRE_PROCESSOR_PATH}/${pickleFileName}`;

    const gzipPickleFileCommand = `gzip ${pickleFilePath}`;
    const gzipPickleFileCommandExec = await exec(gzipPickleFileCommand);

    await addLogToLogList(logListKey, {
      stdout: gzipPickleFileCommandExec.stdout,
      stderr: gzipPickleFileCommandExec.stderr,
    });

    pickleFilePath = `${PRE_PROCESSOR_PATH}/${pickleFileName}.gz`;

    const cpPickleFileCommand = `cp ${pickleFilePath} ${SHARED_FOLDER}`;
    const cpPickleFileCommandExec = await exec(cpPickleFileCommand);

    await addLogToLogList(logListKey, {
      stdout: cpPickleFileCommandExec.stdout,
      stderr: cpPickleFileCommandExec.stderr,
    });

    // delete the pickle file from the processor
    fs.unlinkSync(pickleFilePath);

    await updateExperimentInDashboard(experimentName, {
      status: 'done',
      currentFunction: '',
      completedAt: new Date().toISOString(),
    });

    // remove the file from the uploads folder
    fs.unlinkSync(path);

    // publish a message to the jobs topic to notify the workers
    const message = JSON.stringify({
      experimentName,
      pickleFileName: `${pickleFileName}.gz`,
      redisTopicForJobs,
      config,
    });

    await publishMessageToJobsTopic(REDIS_JOB_NOTIFY_CHANNEL, message);
  } catch (error) {
    await updateExperimentInDashboard(experimentName, {
      status: 'error',
    });
    throw error;
  }
};

module.exports = {
  processUsingPythonProcessor,
};
