import { useEffect, useMemo, useState } from "react";
import { DEMO_PRODUCTS, findDemoProduct } from "../data/demoCatalog";

const STORAGE_KEY = "galantes-demo-cart";

type CartMap = Record<string, number>;

function readCart(): CartMap {
  if (typeof window === "undefined") {
    return {};
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw) as CartMap;
    return parsed ?? {};
  } catch {
    return {};
  }
}

export function useDemoCart() {
  const [cart, setCart] = useState<CartMap>(() => readCart());

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
  }, [cart]);

  const items = useMemo(
    () =>
      Object.entries(cart)
        .map(([productId, quantity]) => {
          const product = findDemoProduct(productId);
          if (!product || quantity <= 0) {
            return null;
          }
          return {
            product,
            quantity,
            subtotalUsd: product.priceUsd * quantity,
          };
        })
        .filter((item): item is NonNullable<typeof item> => item !== null),
    [cart],
  );

  const totals = useMemo(() => {
    const quantity = items.reduce((acc, item) => acc + item.quantity, 0);
    const subtotalUsd = items.reduce((acc, item) => acc + item.subtotalUsd, 0);
    return { quantity, subtotalUsd };
  }, [items]);

  return {
    catalog: DEMO_PRODUCTS,
    items,
    totals,
    add(productId: string) {
      setCart((current) => ({ ...current, [productId]: (current[productId] ?? 0) + 1 }));
    },
    remove(productId: string) {
      setCart((current) => {
        const next = { ...current };
        delete next[productId];
        return next;
      });
    },
    setQuantity(productId: string, quantity: number) {
      setCart((current) => {
        const next = { ...current };
        if (quantity <= 0) {
          delete next[productId];
        } else {
          next[productId] = quantity;
        }
        return next;
      });
    },
    clear() {
      setCart({});
    },
  };
}
