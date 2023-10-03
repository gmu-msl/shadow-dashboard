const fs = require('fs');
const util = require('util');
const exec = util.promisify(require('child_process').exec);

const {
  checkAndReturnExistingExperiment,
  addExperimentToDashboard,
  getExperimentsForDashboard,
} = require('../models/dashboard');

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

const handleUpload = async (req, res) => {
  try {
    // Validate form data
    if (!req.file) {
      return res.redirect('/');
    }

    const form = req.body;
    if (!form.experimentName) {
      return res.redirect('/');
    }

    if (!form.config) {
      return res.redirect('/');
    }

    const { experimentName, config } = req.body;
    const { originalname, filename, path } = req.file;
    const unzippedFolderName = originalname.split('.')[0];

    // Check if experiment already exists
    const experimentHash = await checkAndReturnExistingExperiment(
      experimentName
    );

    console.log(experimentHash);
    if (experimentHash && Object.keys(experimentHash).length > 0) {
      // remove the file from the uploads folder
      fs.unlinkSync(path);

      throw new Error('Experiment already exists');
    }

    const experimentHashToStore = {
      experimentName,
      config,
      originalname,
      filename,
      path,
      unzippedFolderName,
      createdAt: new Date().toISOString(),
      status: 'created',
      currentFunction: '',
    };

    // Store the experiment in redis
    const result = await addExperimentToDashboard(experimentHashToStore);

    // We don't need to wait for the processor to finish
    // We can just redirect the user to the dashboard
    // and let the processor run in the background
    // It will update the status of the experiment in redis
    processUsingPythonProcessor({
      originalFileName: originalname,
      filenameInUploads: filename,
      path,
      experimentName,
      config,
      unzippedFolderName,
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
