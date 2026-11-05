import { useEffect, useState } from "react";

/** Phone-width breakpoint, kept in step with the 560px rules in the CSS. */
const PHONE = "(max-width: 560px)";

/** True while the viewport is phone-width; charts use it to change layout. */
export function useNarrow(query = PHONE): boolean {
  const [narrow, setNarrow] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const update = () => setNarrow(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, [query]);
  return narrow;
}
