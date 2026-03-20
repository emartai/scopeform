type Spinner = {
  start: () => Spinner;
  succeed: (_message?: string) => Spinner;
  stop: () => Spinner;
};

const ora = (): Spinner => {
  const spinner: Spinner = {
    start: () => spinner,
    succeed: () => spinner,
    stop: () => spinner,
  };
  return spinner;
};

export default ora;
