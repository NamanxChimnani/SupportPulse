# Testing / Data Quality

The pipeline has hard gates for:
- unique ticket IDs
- valid customer references
- positive message lengths
- binary target values

For a production version, add:
- schema tests
- null thresholds
- distribution drift checks
- model performance thresholds
- data freshness checks
- unit tests with pytest
- CI on every pull request
