/* dependency-cruiser sample — copy to repo root as .dependency-cruiser.cjs, adapt module names.
   Run: npx depcruise src   (add to verification-gate) */
module.exports = {
  forbidden: [
    { name: "no-circular", severity: "error", comment: "Cycles are always a REVISE (module-boundaries rule 2)",
      from: {}, to: { circular: true } },
    { name: "no-cross-module-internals", severity: "error",
      comment: "Import other modules only via their public index (facade)",
      from: { path: "^src/modules/([^/]+)/" },
      to:   { path: "^src/modules/(?!\\1)([^/]+)/(?!index)" } },
    { name: "transport-stays-thin", severity: "error",
      comment: "Routes/controllers must not import repositories/ORM directly — go through the domain layer",
      from: { path: "^src/(routes|controllers|handlers)/" },
      to:   { path: "^src/(repositories|db|prisma|drizzle)/" } },
  ],
  options: { doNotFollow: { path: "node_modules" }, tsPreCompilationDeps: true },
};
