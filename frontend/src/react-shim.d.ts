declare namespace JSX {
  interface IntrinsicElements {
    [elementName: string]: any;
  }
}

declare module "react" {
  export function useEffect(effect: () => void | (() => void), deps?: any[]): void;
  export function useMemo<T>(factory: () => T, deps?: any[]): T;
  export function useState<T>(initialValue: T): [T, (value: T | ((current: T) => T)) => void];

  const React: any;
  export default React;
}

declare module "react-dom/client" {
  export function createRoot(element: Element): {
    render(node: any): void;
  };
}

declare module "react/jsx-runtime" {
  export const Fragment: any;
  export const jsx: any;
  export const jsxs: any;
}
