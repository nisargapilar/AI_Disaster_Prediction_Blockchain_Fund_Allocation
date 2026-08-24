import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("DisasterReliefModule", (m) => {
  // For now, the trigger authority is your own wallet (the deployer).
  // Later, this can be swapped to a dedicated backend wallet via
  // setTriggerAuthority() without redeploying the contract.
  const triggerAuthority = m.getAccount(0);

  const disasterRelief = m.contract("DisasterRelief", [triggerAuthority]);

  return { disasterRelief };
});