module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  roots: ["<rootDir>/tests"],
  moduleNameMapper: {
    "^chalk$": "<rootDir>/tests/mocks/chalk.ts",
    "^ora$": "<rootDir>/tests/mocks/ora.ts"
  }
};
