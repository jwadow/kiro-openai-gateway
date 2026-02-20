# Motion Core (formerly Framer Motion)

**Import**: `import { motion, AnimatePresence } from 'motion/react'`

## Basic Animation

```tsx
// Simple animate on mount
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.6 }}
/>

// Shorthand (no transition object)
<motion.div animate={{ scale: 1.1 }} />
```

## Variants (Recommended Pattern)

```tsx
const variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

<motion.div
  variants={variants}
  initial="hidden"
  animate="visible"
/>
```

## Gestures

```tsx
<motion.button
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
  whileFocus={{ outline: '2px solid blue' }}
/>

// Drag
<motion.div
  drag
  dragConstraints={{ left: 0, right: 300 }}
  dragElastic={0.2}
/>
```

## Layout Animations

```tsx
// Automatic layout animation
<motion.div layout />

// Shared layout
<motion.div layoutId="shared-element" />

// Layout with spring
<motion.div layout transition={{ type: 'spring', stiffness: 300 }} />
```

## Exit Animations (AnimatePresence)

```tsx
import { AnimatePresence } from 'motion/react';

<AnimatePresence>
  {isVisible && (
    <motion.div
      key="modal"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    />
  )}
</AnimatePresence>
```

## Stagger Children

```tsx
const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

<motion.ul variants={container} initial="hidden" animate="visible">
  {items.map(i => <motion.li key={i} variants={item} />)}
</motion.ul>
```

## Transition Types

```tsx
// Spring (default for physical properties)
transition={{ type: 'spring', stiffness: 300, damping: 20 }}

// Tween
transition={{ type: 'tween', duration: 0.5, ease: 'easeInOut' }}

// Inertia (for drag)
transition={{ type: 'inertia', velocity: 50 }}
```

## Common Easing

```tsx
ease: 'linear'
ease: 'easeIn' | 'easeOut' | 'easeInOut'
ease: 'circIn' | 'circOut' | 'circInOut'
ease: 'backIn' | 'backOut' | 'backInOut'
ease: [0.4, 0, 0.2, 1]  // cubic-bezier
```

## useAnimate Hook

```tsx
import { useAnimate } from 'motion/react';

function Component() {
  const [scope, animate] = useAnimate();
  
  const handleClick = async () => {
    await animate(scope.current, { x: 100 });
    await animate(scope.current, { scale: 1.2 });
  };
  
  return <div ref={scope} onClick={handleClick} />;
}
```

## Motion Values

```tsx
import { useMotionValue, useTransform } from 'motion/react';

const x = useMotionValue(0);
const opacity = useTransform(x, [0, 100], [1, 0]);

<motion.div style={{ x, opacity }} drag="x" />
```

## Integration with Tailwind

```tsx
// Motion handles animation, Tailwind handles styling
<motion.div
  className="bg-blue-500 rounded-lg p-4"
  whileHover={{ scale: 1.05 }}
  transition={{ type: 'spring' }}
/>
```

## Validation Checklist

- [ ] Import from `motion/react` (not `framer-motion`)
- [ ] Use variants for complex animations
- [ ] Wrap conditional renders with `AnimatePresence`
- [ ] Add `key` prop to animated elements in `AnimatePresence`
- [ ] Use `layout` for automatic layout animations
- [ ] Prefer `whileHover`/`whileTap` over CSS `:hover`
