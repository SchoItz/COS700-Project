import { useEffect, useRef, useState, type DependencyList } from "react";

export interface ApiState<T> {
  data: T | null;
  error: string | null;
  /** The backend answered 404: the thing asked for does not exist. */
  notFound: boolean;
  loading: boolean;
}

/** Runs `fetcher` whenever `deps` change and tracks its result. A response
 * that arrives after the deps have changed again is discarded, so quick
 * navigation can never show the previous page's data. */
export function useApi<T>(fetcher: () => Promise<T>, deps: DependencyList): ApiState<T> {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    error: null,
    notFound: false,
    loading: true,
  });

  // The caller's deps (route params, a selected metric) decide when to
  // refetch; the latest fetcher is read through a ref so it need not be stable.
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;
  const key = JSON.stringify(deps);

  useEffect(() => {
    let current = true;
    setState({ data: null, error: null, notFound: false, loading: true });
    fetcherRef.current()
      .then((data) => current && setState({ data, error: null, notFound: false, loading: false }))
      .catch((e: unknown) => {
        if (!current) return;
        const status = (e as { response?: { status?: number } })?.response?.status;
        setState({ data: null, error: String(e), notFound: status === 404, loading: false });
      });
    return () => {
      current = false;
    };
  }, [key]);

  return state;
}
