const Schema = require('mongoose').Schema;
const mongoose = require('mongoose');

const userResultsSchema = new Schema({
  username: String,
  results: [
    {
      experimentName: String,
      relativeCoefficient: Number,
      ipGuessed: String,
      file: String,
      feature: String,
      accuracy: Number,
      recallAt2: Number,
      recallAt4: Number,
      recallAt8: Number,
      avgRank: Number,
    },
  ],
});

const UserResults = mongoose.model('UserResults', userResultsSchema);

module.exports = UserResults;
