// This is a service file that will be used by the controller to process the file.
const fs = require('fs');
const util = require('util');
const exec = util.promisify(require('child_process').exec);

const { updateExperimentInDashboard } = require('../models/dashboard');

const processUsingPythonProcessor = async ({
  originalFileName,
  filenameInUploads,
  path,
  experimentName,
  config,
  unzippedFolderName,
}) => {
  try {
    // update the experiment to say processing
    await updateExperimentInDashboard(experimentName, {
      status: 'processing',
    });

    const processorPath = './processors/preprocess-python';
    // 1. Move file to processor (tmp with the experiment name)
    const processorFilePath = `./processors/preprocess-python/${experimentName}`;

    if (!fs.existsSync(processorFilePath)) {
      fs.mkdirSync(processorFilePath, { recursive: true });
    }

    fs.copyFileSync(path, `${processorFilePath}/${originalFileName}`);

    // 2. unzip file
    const unzipCommand = `unzip ${processorFilePath}/${originalFileName} -d ${processorFilePath}`;
    const unzipCommandExec = await exec(unzipCommand);

    // 3. remove the zip file, we don't need it anymore
    fs.unlinkSync(`${processorFilePath}/${originalFileName}`);

    // 4. create csv folder and server_log folder in the unzipped folder
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

    console.log(pcapToCsvCommandExec);

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
    const processorCommand = `cd ${processorPath} && python3 loadFilesAndGeneratePickle.py ${configFileParam} ${experimentName} ${csvFolderParam} ${serverLogFolderParam} localhost ${experimentName}`;
    const processorCommandExec = await exec(processorCommand);

    console.log(processorCommandExec);
    await updateExperimentInDashboard(experimentName, {
      status: 'done',
      currentFunction: '',
    });
  } catch (error) {
    throw error;
  }
};

module.exports = {
  processUsingPythonProcessor,
};
