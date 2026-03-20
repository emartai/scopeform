const passthrough = (value: string) => value;

const chalk = {
  green: passthrough,
  red: passthrough,
  yellow: passthrough,
  bold: {
    red: passthrough,
    yellow: passthrough,
  },
};

export default chalk;
