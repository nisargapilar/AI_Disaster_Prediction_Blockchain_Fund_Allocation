import { useContext } from "react";
import { AuthContext } from "./contextObject";

export function useAuth() {
  return useContext(AuthContext);
}
