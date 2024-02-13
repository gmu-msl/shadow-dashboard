const { getExperimentForViewExperiment } = require('../models/experiment');
const UserResults = require('../models/userResults');
const {
  getExperimentResults,
  postProcessUsingPython,
} = require('../services/processResults');

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
      completed:
        parseInt(experiment.jobsCompleted) === parseInt(experiment.jobsCreated),
    });
  } catch (error) {
    res.render('experiment', {
      title: 'Experiment',
      error: error.message,
      message: '',
    });
  }
};

const viewExperimentResults = async (req, res) => {
  try {
    const { experimentName } = req.params;
    const { username } = req.query;

    const experiment = await getExperimentForViewExperiment(experimentName);
    const experimentCompleted =
      parseInt(experiment.jobsCompleted) === parseInt(experiment.jobsCreated);
    const [resultsExist, results] = await getExperimentResults(experimentName);

    if (!experiment) {
      throw new Error('Experiment does not exist');
    }

    let userResults = {};
    let totalUserResults = 0;
    let resultsObject = {};
    if (username && username !== '') {
      // userResults = await UserResults.findOne(
      //   { username },
      //   { results: { $slice: 100 }, total: { $size: '$results' } }
      // );
      userResults = await UserResults.aggregate([
        { $match: { username } },
        {
          $project: {
            results: {
              $slice: [
                {
                  $filter: {
                    input: '$results',
                    as: 'result',
                    cond: {
                      $eq: ['$$result.experimentName', experimentName],
                    },
                  },
                },
                100,
              ], // limit_number is the number of elements you want to keep
            },
            total: { $size: '$results' },
          },
        },
      ]);

      if (userResults) {
        userResults = userResults[0];
        totalUserResults = userResults.total;
      }

      if (userResults && userResults.results) {
        let rank = 1;
        for (let i = 0; i < userResults.results.length; i++) {
          const { ipGuessed } = userResults.results[i];

          if (resultsObject[ipGuessed]) {
            resultsObject[ipGuessed].features.push(
              userResults.results[i].feature
            );
          } else {
            resultsObject[ipGuessed] = {
              features: [userResults.results[i].feature],
              ipGuessed,
              rank,
            };
            rank += 1;
          }

          if (Object.keys(resultsObject).length > 10) {
            break;
          }
        }
      }
    }

    console.log(userResults);

    return res.render('experimentResult', {
      title: 'Search Results',
      error: '',
      message: '',
      experiment,
      resultsExist,
      results,
      usernameSearch: username === undefined ? '' : username,
      userResults,
      userResultExists: userResults ? userResults.results?.length > 0 : false,
      totalUserResults,
      currentTotalUserResults: userResults ? userResults.results?.length : 0,
      resultsObject: userResults ? resultsObject : {},
      completed: experimentCompleted,
    });
  } catch (error) {
    console.log(error);
    res.render('experimentResult', {
      title: 'Search Results',
      error: error.message,
      message: '',
    });
  }
};

const processResults = async (req, res) => {
  try {
    const { experimentName } = req.params;

    const experiment = await getExperimentForViewExperiment(experimentName);

    const [running, status] = await postProcessUsingPython(experimentName);

    if (running) {
      return res.render('experimentResult', {
        title: 'Experiment Result',
        error: '',
        message: 'Processing in progress',
        experiment,
        resultsExist: false,
        results: { message: `Processing in progress - ${status}` },
        status,
      });
    }
  } catch (error) {
    res.render('experimentResult', {
      title: 'Experiment Result',
      error: error.message,
      message: '',
    });
  }
};

module.exports = {
  viewExperiment,
  viewExperimentResults,
  processResults,
};
