"""
Meteorological Pipeline Dependency Validator.

This module provides the `PipelineValidator` class, which ensures that a 
given NetCDF dataset contains the necessary variables (or their precursors) 
to fulfill a requested calculation recipe. It uses recursive backtracking 
to resolve complex multi-step dependencies.
"""

import re
import traceback
import itertools

from src.libs.meteo_functions.recipes import PIPELINE_RECIPES
from src.libs.netcdf_functions.dataset_inventory import DatasetInventory


class PipelineValidator:
    """Validates data availability for calculation pipelines.

    Uses recursive logic to check if a requested target metric can be 
    computed using available raw variables and defined recipe pathways.
    """
    def __init__(self, inventory: DatasetInventory):
        self.inventory = inventory

    def _find_raw_variable_by_token(self, keyword_token: str) -> str | None:
        """Helper to match a token keyword against cached inventory metadata or spatial dimensions."""
        token_lower = keyword_token.lower()

        try:
            # --- DEFENSIVE INTERCEPT FOR DIMENSION LOOKUPS ---
            if token_lower in ["pressure_level", "isobaricinhpa", "level", "plev"]:
                pressure_keys = ["isobaricInhPa", "pressure_level", "plev", "level"]
                p_coord = next((k for k in pressure_keys if k in self.inventory.dimensions), None)
                if p_coord:
                    return p_coord

            if token_lower in ["time", "valid_time", "t", "times"]:
                time_keys = ["time", "valid_time", "t", "times"]
                t_coord = next((k for k in time_keys if k in self.inventory.dimensions), None)
                if t_coord:
                    return t_coord
        except (AttributeError, TypeError) as e:
            print(f"[ERROR] Failed checking inventory dimensions for token '{keyword_token}': {e}")

        try:
            for var_name, meta in self.inventory.variables.items():
                if token_lower == var_name.lower():
                    return var_name

                attrs = getattr(meta, "attributes", None) or {}
                if token_lower == attrs.get("GRIB_shortName", "").lower():
                    return var_name

                descriptive_text = (
                    f"{attrs.get('long_name', '')} "
                    f"{attrs.get('GRIB_name', '')} "
                    f"{attrs.get('standard_name', '')}"
                ).lower()

                tokens = set(re.findall(r'[a-z0-9_]+', descriptive_text))
                if token_lower in tokens:
                    return var_name
        except (AttributeError, TypeError) as e:
            print(f"[ERROR] Exception occurred scanning variables for token '{keyword_token}': {e}")
            traceback.print_exc()

        return None

    def resolve_valid_recipe_tree(self, target: str, visited: set[str] | None = None) -> dict | None:
        """Recursively determines if a calculation target can be fulfilled.

        Args:
            target: The name of the variable to resolve.
            visited: Set of already visited nodes to prevent circular dependencies.

        Returns:
            dict | None: The viable recipe dictionary, or None if impossible.
        """
        if visited is None:
            visited = set()

        if target in visited:
            return None  # Circular dependency guard
        visited.add(target)

        # Base Case: It's a raw variable sitting directly inside the NetCDF file
        if self._find_raw_variable_by_token(target):
            return {"type": "raw_file"}

        try:
            if target in PIPELINE_RECIPES:
                for option in PIPELINE_RECIPES[target]:
                    dependencies_dict = option.get("depends_on", {})
                    if not isinstance(dependencies_dict, dict):
                        continue

                    option_is_viable = True
                    for dep_token in dependencies_dict.keys():
                        if not self.resolve_valid_recipe_tree(dep_token, visited.copy()):
                            option_is_viable = False
                            break

                    if option_is_viable:
                        return option
        except Exception as e:
            print(f"[ERROR] Critical failure resolving recipe tree path for target '{target}': {e}")
            traceback.print_exc()

        return None

    def _resolve_missing_alternatives(self, target: str, visited: set[str] | None = None) -> list[set[str]]:
        """
        Recursively maps all combination sets of primitive variables that could satisfy the target.
        """
        if visited is None:
            visited = set()

        if target in visited:
            return []
        visited.add(target)

        # Base case: Variable is already provided directly in the file
        if self._find_raw_variable_by_token(target):
            return [set()]

        # Option A: Satisfy this node by providing it directly as a primitive token
        pathway_options = [{target}]

        # Option B: Evaluate the mathematical recipe dependencies required to compute it
        if target in PIPELINE_RECIPES:
            for option in PIPELINE_RECIPES[target]:
                dep_lists = []
                for dep in option.get("depends_on", {}).keys():
                    res = self._resolve_missing_alternatives(dep, visited.copy())
                    if not res:
                        dep_lists = None
                        break
                    dep_lists.append(res)

                # Cross-multiply alternative combinations for the dependencies (AND logic)
                if dep_lists is not None:
                    for combo in itertools.product(*dep_lists):
                        merged_set = set()
                        for s in combo:
                            merged_set.update(s)
                        pathway_options.append(merged_set)

        # Deduplicate sets
        unique_options = []
        for s in pathway_options:
            if s not in unique_options:
                unique_options.append(s)

        # Prune sets down to the minimum requirements (remove redundant supersets)
        pruned_options = []
        for s in unique_options:
            if not any(other < s for other in unique_options if other != s):
                pruned_options.append(s)

        return pruned_options

    def validate_pipeline_readiness(self, target_outputs: list[str]) -> dict[str, str]:
        """Validates that the inventory can satisfy all target output requirements.

        Scans all requirements to guarantee the file matches runtime 
        dependencies.

        Args:
            target_outputs: List of requested target variable names.

        Returns:
            dict[str, str]: A mapping of required tokens to their actual 
                NetCDF variable names.

        Raises:
            ValueError: If any target cannot be resolved, with detailed 
                diagnostics of missing alternatives.
        """
        resolved_mapping = {}
        failure_diagnostics = {}

        def gather_raw_leaves(target_variable: str):
            try:
                recipe = self.resolve_valid_recipe_tree(target_variable)
                if not recipe:
                    # Collect combinations of missing requirements
                    alternatives = self._resolve_missing_alternatives(target_variable)

                    # Filter out the root target_variable token itself from options to keep errors focused on primitives
                    pruned_alts = []
                    for alt in alternatives:
                        clean_alt = {p for p in alt if p != target_variable}
                        if clean_alt and clean_alt not in pruned_alts:
                            pruned_alts.append(clean_alt)

                    # Convert to strings
                    formatted = []
                    for alt in pruned_alts:
                        formatted.append(f"[{', '.join(f"'{p}'" for p in sorted(list(alt)))}]")

                    failure_diagnostics[target_variable] = formatted
                    return

                if recipe.get("type") == "raw_file":
                    actual_name = self._find_raw_variable_by_token(target_variable)
                    if actual_name:
                        resolved_mapping[target_variable] = actual_name
                else:
                    depends_on = recipe.get("depends_on", {})
                    if hasattr(depends_on, "keys"):
                        for dep in depends_on.keys():
                            gather_raw_leaves(dep)
            except Exception as e:
                failure_diagnostics[target_variable] = [f"Critical execution crash: {e}"]

        for target in target_outputs:
            gather_raw_leaves(target)

        if failure_diagnostics:
            error_msg = ["\nPipeline validation failed! Unresolvable calculation pathways.", "To run this pipeline, update your NetCDF file to include one of these variable options:"]

            for target_token, pathways in failure_diagnostics.items():
                error_msg.append(f"\n❌ Target Variable Request: '{target_token}'")
                error_msg.append(f"   ↳ Missing variable option combo: {" OR ".join(pathways)}")

            raise ValueError("\n".join(error_msg))

        return resolved_mapping
