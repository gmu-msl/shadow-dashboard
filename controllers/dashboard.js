const fs = require('fs');
const util = require('util');
const exec = util.promisify(require('child_process').exec);
const crypto = require('crypto');

const {
  checkAndReturnExistingExperiment,
  addExperimentToDashboard,
  getExperimentsForDashboard,
  experimentObject,
} = require('../models/experiment');

const {
  processUsingPythonProcessor,
} = require('../services/processFileUsingProcessors');

const viewDashboard = async (req, res) => {
  try {
    const experiments = await getExperimentsForDashboard();
    return res.render('index', {
      title: 'Dashboard',
      error: '',
      message: '',
      experiments,
    });
  } catch (error) {
    console.log(error);
    return res.render('index', {
      title: 'Dashboard',
      error: error.message,
      message: '',
    });
  }
};

/**
 *
 * @param {*} req express request object
 * @param {*} res express response object
 * @returns render the dashboard with the updated experiments list if successful
 * @returns render the dashboard with an error message if unsuccessful
 */
const handleUpload = async (req, res) => {
  try {
    // Validate form data
    if (
      !req.file &&
      !req.body.fileLink &&
      !req.body.pickleFile &&
      !req.body.pickleFileLink
    ) {
      // if either zip file or pickle file or their links are not present, then redirect to the dashboard
      return res.redirect('/');
    }

    // if both zip file and pickle file are present, then redirect to the dashboard, because we only need one of them
    if (
      req.file &&
      req.body.pickleFile &&
      req.body.pickleFileLink &&
      req.body.fileLink
    ) {
      return res.redirect('/');
    }

    const form = req.body;
    if (!form.experimentName) {
      return res.redirect('/');
    }

    if (!form.config) {
      return res.redirect('/');
    }

    const { fileLink } = req.body;

    // if picklefile or picklefile link is given, we need not run the entire process
    // but we just run the generate tasks from the pickle file.

    let originalname = '';
    let filename = '';
    let path = '';

    // if fileLink is not empty, then download the file ourselves into the uploads folder
    if (fileLink) {
      originalname = `${crypto.randomUUID().toString()}.zip`;
      filename = crypto.randomUUID().toString();
      path = `uploads/${originalname}`;
      const curlCommandToDownload = `curl -o uploads/${originalname} ${fileLink}`;
      const curlCommandToDownloadExec = await exec(curlCommandToDownload);
      console.log(curlCommandToDownloadExec);
    } else {
      originalname = req.file.originalname;
      filename = req.file.filename;
      path = req.file.path;
    }

    const { experimentName, config } = req.body;

    const checkUnzippedFolderNameInZipCommand = `unzip -qql ${path} | head -n1 | tr -s ' ' | cut -d' ' -f5-`;
    const checkUnzippedFolderNameInZipCommandExec = await exec(
      checkUnzippedFolderNameInZipCommand
    );

    const unzippedFolderName = checkUnzippedFolderNameInZipCommandExec.stdout
      .split('/')[0]
      .trim();

    // Check if experiment already exists
    const experimentHash = await checkAndReturnExistingExperiment(
      experimentName
    );

    if (experimentHash && Object.keys(experimentHash).length > 0) {
      // remove the file from the uploads folder
      fs.unlinkSync(path);

      throw new Error('Experiment already exists');
    }

    const randomUUID = crypto.randomUUID().toString();
    const pickleFileName = `${experimentName}-${randomUUID}.pkl`;
    const logListKey = `${experimentName}-${randomUUID}-log-list`;

    // Create the experiment object using the experimentObjectStructure
    const experimentHashToStore = new experimentObject({
      experimentName,
      config,
      originalname,
      filename,
      path,
      unzippedFolderName,
      createdAt: new Date().toISOString(),
      completedAt: '',
      pickleFile: pickleFileName,
      status: 'created',
      currentFunction: '',
      logListKey: logListKey,
      jobsTopic: `${experimentName}-${randomUUID}`,
      jobsCreated: 0,
    });

    // Store the experiment in redis
    const result = await addExperimentToDashboard(experimentHashToStore);

    // We don't need to wait for the processor to finish
    // We can just redirect the user to the dashboard
    // and let the processor run in the background
    // It will update the status of the experiment in redis
    processUsingPythonProcessor({
      originalFileName: originalname,
      path,
      experimentName,
      config,
      unzippedFolderName,
      pickleFileName,
      redisTopicForJobs: `${experimentName}-${randomUUID}`,
      logListKey,
    });

    // Redirect the user to the dashboard
    return res.redirect('/');
  } catch (error) {
    console.log(error);
    return res.redirect('/');
  }
};

module.exports = {
  viewDashboard,
  handleUpload,
};
