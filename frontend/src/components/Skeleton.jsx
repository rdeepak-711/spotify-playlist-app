import { motion } from "framer-motion";

export default function Skeleton({ className = "", ...props }) {
  return (
    <motion.div
      className={`bg-gray-800 animate-pulse ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      {...props}
    />
  );
}
