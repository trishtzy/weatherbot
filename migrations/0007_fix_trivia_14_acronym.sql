-- Migration 0007: Expand NWP acronym in trivia fact 14
-- Show long form first, then acronym in brackets

UPDATE trivia
SET text = 'Very fast high-performance computers are required to carry out the enormous number of calculations required by Numerical Weather Prediction (NWP) models.'
WHERE id = 14;

PRAGMA user_version=7;
