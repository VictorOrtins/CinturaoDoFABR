import "@testing-library/jest-dom/vitest";

// recharts' <ResponsiveContainer> sizes itself via ResizeObserver + getBoundingClientRect,
// neither of which jsdom implements with real layout — without these it stays at 0x0 and
// none of its children ever mount.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
Element.prototype.getBoundingClientRect = () =>
  ({
    width: 600,
    height: 400,
    top: 0,
    left: 0,
    bottom: 0,
    right: 0,
    x: 0,
    y: 0,
    toJSON() {},
  }) as DOMRect;
