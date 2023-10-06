const { getExperimentForViewExperiment } = require('../models/experiment');

const viewExperiment = async (req, res) => {
  try {
    const { experimentName } = req.params;

    const experiment = await getExperimentForViewExperiment(experimentName);

    if (!experiment) {
      throw new Error('Experiment does not exist');
    }

    return res.render('experiment', {
      title: 'Experiment',
      error: '',
      message: '',
      experiment,
    });
  } catch (error) {
    res.render('experiment', {
      title: 'Experiment',
      error: error.message,
      message: '',
    });
  }
};

module.exports = {
  viewExperiment,
};
