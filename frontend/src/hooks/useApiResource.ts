import { useCallback, useEffect, useRef, useState } from 'react';
import type { DataSource } from '../types';

export function useApiResource<T>(loader: () => Promise<T>, fallback: T, dependencyKey = 'default') {
  const loaderRef = useRef(loader);
  loaderRef.current = loader;
  const [data, setData] = useState<T>(fallback);
  const [source, setSource] = useState<DataSource>('fallback');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const result = await loaderRef.current();
      setData(result);
      setSource('api');
      setError(null);
    } catch (reason) {
      setSource('fallback');
      setError(reason instanceof Error ? reason.message : 'Falha ao carregar os dados locais.');
    } finally {
      setLoading(false);
    }
  }, [dependencyKey]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    const onOnline = () => void reload();
    window.addEventListener('online', onOnline);
    return () => window.removeEventListener('online', onOnline);
  }, [reload]);

  return { data, setData, source, loading, error, reload };
}
