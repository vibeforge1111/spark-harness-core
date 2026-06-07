declare module 'node:crypto' {
  export function createHmac(
    algorithm: string,
    key: string
  ): {
    update(data: string, inputEncoding?: string): {
      digest(encoding: 'hex'): string;
    };
  };

  export function randomUUID(): string;
}
