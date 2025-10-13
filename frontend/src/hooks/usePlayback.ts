import { useCallback, useEffect, useRef, useState } from 'react';

export function usePlayback(maxIndex: number, initialSpeed = 400) {
  const [index, setIndex] = useState(maxIndex > 0 ? maxIndex - 1 : 0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(initialSpeed);
  const frameRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (frameRef.current) {
      clearInterval(frameRef.current);
      frameRef.current = null;
    }
  }, []);

  const play = useCallback(() => {
    if (maxIndex <= 0) return;
    setIsPlaying(true);
  }, [maxIndex]);

  const pause = useCallback(() => {
    setIsPlaying(false);
  }, []);

  const toggle = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  const step = useCallback(
    (direction: 1 | -1) => {
      setIndex((prev) => {
        if (maxIndex === 0) return prev;
        const next = prev + direction;
        if (next < 0) return 0;
        if (next >= maxIndex) return maxIndex - 1;
        return next;
      });
    },
    [maxIndex],
  );

  const goToStart = useCallback(() => {
    setIndex(0);
  }, []);

  const goToEnd = useCallback(() => {
    if (maxIndex > 0) {
      setIndex(maxIndex - 1);
    }
  }, [maxIndex]);

  useEffect(() => {
    if (!isPlaying) {
      clearTimer();
      return;
    }
    if (maxIndex === 0) return;

    clearTimer();
    frameRef.current = setInterval(() => {
      setIndex((prev) => {
        if (prev >= maxIndex - 1) {
          return maxIndex - 1;
        }
        return prev + 1;
      });
    }, speed);

    return () => {
      clearTimer();
    };
  }, [isPlaying, maxIndex, speed, clearTimer]);

  useEffect(() => {
    // Reset index when dataset size changes.
    if (maxIndex === 0) {
      setIndex(0);
      setIsPlaying(false);
      return;
    }
    setIndex(maxIndex - 1);
  }, [maxIndex]);

  useEffect(() => () => clearTimer(), [clearTimer]);

  return {
    index,
    isPlaying,
    speed,
    setSpeed,
    play,
    pause,
    toggle,
    stepForward: () => step(1),
    stepBackward: () => step(-1),
    goToStart,
    goToEnd,
    setIndex,
  };
}
