#!/usr/bin/env python3
"""
Statistics Service for Granger Causality Analysis

This service provides statistical analysis functionality including:
- Outlier detection and removal
- Normality testing
- Assumption testing (homogeneity, sphericity, heteroscedasticity)
- ANOVA analysis
- Post-hoc testing
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd, MultiComparison
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.power import TTestPower, FTestPower
import pingouin as pg
from typing import Dict, List, Tuple, Optional, Any, Union
import warnings

warnings.filterwarnings("ignore")


class StatisticsService:
    """Service for statistical analysis operations"""

    def __init__(self):
        self.last_extracted_data = None

    def extract_data_for_analysis(
        self, analyzer, metric_type: str, variable: str
    ) -> Optional[pd.DataFrame]:
        """
        Extract data from analyzer for statistical analysis

        Args:
            analyzer: GrangerCausalityAnalyzer instance
            metric_type: Type of metric ('Global', 'Nodal', 'Pairwise')
            variable: Variable name to extract

        Returns:
            DataFrame with columns: Participant, Condition, Timepoint, Value
        """
        if not analyzer.analyses:
            return None

        data_rows = []

        for key, analysis in analyzer.analyses.items():
            metadata = analysis["metadata"]
            participant_id = metadata.get("participant_id", "Unknown")
            condition = metadata.get("condition", "Unknown")
            timepoint = metadata.get("timepoint", "Unknown")

            try:
                if metric_type == "Global":
                    if variable in analysis["global"]:
                        value = analysis["global"][variable]
                        if pd.notna(value) and np.isfinite(value):
                            data_rows.append(
                                {
                                    "Participant": participant_id,
                                    "Condition": condition,
                                    "Timepoint": timepoint,
                                    "Value": float(value),
                                }
                            )

                elif metric_type == "Nodal":
                    if variable in analysis["nodal"]:
                        nodal_data = analysis["nodal"][variable]
                        if isinstance(nodal_data, dict):
                            # Average across nodes
                            values = [
                                v
                                for v in nodal_data.values()
                                if pd.notna(v) and np.isfinite(v)
                            ]
                            if values:
                                avg_value = np.mean(values)
                                data_rows.append(
                                    {
                                        "Participant": participant_id,
                                        "Condition": condition,
                                        "Timepoint": timepoint,
                                        "Value": float(avg_value),
                                    }
                                )
                        elif pd.notna(nodal_data) and np.isfinite(nodal_data):
                            data_rows.append(
                                {
                                    "Participant": participant_id,
                                    "Condition": condition,
                                    "Timepoint": timepoint,
                                    "Value": float(nodal_data),
                                }
                            )

                elif metric_type == "Pairwise":
                    if variable in analysis["pairwise"]:
                        pairwise_data = analysis["pairwise"][variable]
                        if isinstance(pairwise_data, dict):
                            # Average across connections
                            values = []
                            for connections in pairwise_data.values():
                                if isinstance(connections, dict):
                                    for v in connections.values():
                                        if pd.notna(v) and np.isfinite(v):
                                            values.append(v)
                                elif pd.notna(connections) and np.isfinite(connections):
                                    values.append(connections)

                            if values:
                                avg_value = np.mean(values)
                                data_rows.append(
                                    {
                                        "Participant": participant_id,
                                        "Condition": condition,
                                        "Timepoint": timepoint,
                                        "Value": float(avg_value),
                                    }
                                )
                        elif pd.notna(pairwise_data) and np.isfinite(pairwise_data):
                            data_rows.append(
                                {
                                    "Participant": participant_id,
                                    "Condition": condition,
                                    "Timepoint": timepoint,
                                    "Value": float(pairwise_data),
                                }
                            )

            except Exception as e:
                print(f"Error extracting data for {key}: {e}")
                continue

        if not data_rows:
            return None

        df = pd.DataFrame(data_rows)
        self.last_extracted_data = df.copy()
        return df

    def detect_outliers_zscore(
        self, df: pd.DataFrame, threshold: float = 3.0
    ) -> pd.DataFrame:
        """
        Detect outliers using Z-score method

        Args:
            df: DataFrame with Value column
            threshold: Z-score threshold (default 3.0)

        Returns:
            DataFrame with additional 'is_outlier' and 'z_score' columns
        """
        result_df = df.copy()

        mean_val = df["Value"].mean()
        std_val = df["Value"].std()

        if std_val > 0:
            result_df["z_score"] = abs((df["Value"] - mean_val) / std_val)
            result_df["is_outlier"] = result_df["z_score"] > threshold
        else:
            result_df["z_score"] = 0.0
            result_df["is_outlier"] = False

        return result_df

    def detect_outliers_iqr(
        self, df: pd.DataFrame, multiplier: float = 1.5
    ) -> pd.DataFrame:
        """
        Detect outliers using IQR method

        Args:
            df: DataFrame with Value column
            multiplier: IQR multiplier (default 1.5)

        Returns:
            DataFrame with additional 'is_outlier' column
        """
        result_df = df.copy()

        q1 = df["Value"].quantile(0.25)
        q3 = df["Value"].quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr

        result_df["is_outlier"] = (df["Value"] < lower_bound) | (
            df["Value"] > upper_bound
        )
        result_df["lower_bound"] = lower_bound
        result_df["upper_bound"] = upper_bound

        return result_df

    def remove_outliers(
        self, df: pd.DataFrame, method: str = "mean"
    ) -> Tuple[pd.DataFrame, int]:
        """
        Remove outliers using mean or median imputation
        
        This method applies multiple imputation technique by replacing outlier values
        with the mean or median of non-outlier values, effectively neutralizing
        the effect of extreme outliers while preserving sample size.

        Args:
            df: DataFrame with 'is_outlier' column and 'Value' column
            method: Replacement method ('mean' or 'median')

        Returns:
            Tuple of (cleaned DataFrame, number of outliers imputed)
        """
        result_df = df.copy()
        outlier_mask = df["is_outlier"]
        outlier_count = outlier_mask.sum()

        if outlier_count > 0:
            # Calculate replacement value from non-outlier data
            non_outlier_values = df.loc[~outlier_mask, "Value"]
            
            if method == "mean":
                replacement_value = non_outlier_values.mean()
                print(f"Mean imputation: Replacing {outlier_count} outliers with mean value {replacement_value:.4f}")
            else:  # median
                replacement_value = non_outlier_values.median()
                print(f"Median imputation: Replacing {outlier_count} outliers with median value {replacement_value:.4f}")

            # Apply imputation
            result_df.loc[outlier_mask, "Value"] = replacement_value
            
            # Log the imputation details
            print(f"Successfully applied {method} imputation to neutralize {outlier_count} outlier(s)")

        return result_df, outlier_count

    def test_normality(
        self, df: pd.DataFrame, group_by: str = "none"
    ) -> List[Dict[str, Any]]:
        """
        Test normality using Shapiro-Wilk test

        Args:
            df: DataFrame with Value column and grouping variables
            group_by: Grouping method ('none', 'condition', 'timepoint', 'both')

        Returns:
            List of test results dictionaries
        """
        results = []

        if group_by == "none":
            if len(df) >= 3:
                stat, p = stats.shapiro(df["Value"])
                results.append(
                    {
                        "group": "All data",
                        "n": len(df),
                        "statistic": stat,
                        "p_value": p,
                        "is_normal": p > 0.05,
                    }
                )

        elif group_by == "condition":
            for condition, group in df.groupby("Condition"):
                if len(group) >= 3:
                    stat, p = stats.shapiro(group["Value"])
                    results.append(
                        {
                            "group": f"Condition: {condition}",
                            "n": len(group),
                            "statistic": stat,
                            "p_value": p,
                            "is_normal": p > 0.05,
                        }
                    )

        elif group_by == "timepoint":
            for timepoint, group in df.groupby("Timepoint"):
                if len(group) >= 3:
                    stat, p = stats.shapiro(group["Value"])
                    results.append(
                        {
                            "group": f"Timepoint: {timepoint}",
                            "n": len(group),
                            "statistic": stat,
                            "p_value": p,
                            "is_normal": p > 0.05,
                        }
                    )

        elif group_by == "both":
            for (condition, timepoint), group in df.groupby(["Condition", "Timepoint"]):
                if len(group) >= 3:
                    stat, p = stats.shapiro(group["Value"])
                    results.append(
                        {
                            "group": f"{condition} × {timepoint}",
                            "n": len(group),
                            "statistic": stat,
                            "p_value": p,
                            "is_normal": p > 0.05,
                        }
                    )

        return results

    def test_homogeneity_levene(self, df: pd.DataFrame, factor: str) -> Dict[str, Any]:
        """
        Test homogeneity of variance using Levene's test

        Args:
            df: DataFrame with Value column and factor column
            factor: Factor column name ('Condition' or 'Timepoint')

        Returns:
            Dictionary with test results
        """
        try:
            groups = [group["Value"].values for name, group in df.groupby(factor)]
            if len(groups) >= 2 and all(len(g) >= 2 for g in groups):
                stat, p = stats.levene(*groups)
                return {
                    "test": f"Levene's Test ({factor})",
                    "statistic": stat,
                    "p_value": p,
                    "assumption_met": p > 0.05,
                    "interpretation": (
                        "Homogeneity assumed" if p > 0.05 else "Homogeneity violated"
                    ),
                }
        except Exception as e:
            print(f"Error in Levene's test: {e}")

        return {
            "test": f"Levene's Test ({factor})",
            "statistic": np.nan,
            "p_value": np.nan,
            "assumption_met": False,
            "interpretation": "Could not compute",
        }

    def test_sphericity_mauchly(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Test sphericity using Mauchly's test (simplified implementation)

        Args:
            df: DataFrame in long format

        Returns:
            Dictionary with test results
        """
        try:
            # Use pingouin for sphericity test if available
            # This is a simplified implementation
            pivot_df = df.pivot_table(
                values="Value", index="Participant", columns="Timepoint", aggfunc="mean"
            )

            if pivot_df.shape[1] >= 3:  # Need at least 3 time points
                # Use pingouin's sphericity test
                spher = pg.sphericity(pivot_df.values)
                return {
                    "test": "Mauchly's Test (Sphericity)",
                    "statistic": spher["W"],
                    "p_value": spher["pval"],
                    "assumption_met": spher["pval"] > 0.05,
                    "interpretation": (
                        "Sphericity assumed"
                        if spher["pval"] > 0.05
                        else "Sphericity violated"
                    ),
                }
        except Exception as e:
            print(f"Error in Mauchly's test: {e}")

        return {
            "test": "Mauchly's Test (Sphericity)",
            "statistic": np.nan,
            "p_value": np.nan,
            "assumption_met": False,
            "interpretation": "Could not compute (need ≥3 timepoints)",
        }

    def test_heteroscedasticity_breusch_pagan(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Test heteroscedasticity using Breusch-Pagan test

        Args:
            df: DataFrame with Value and factor columns

        Returns:
            Dictionary with test results
        """
        try:
            # Create dummy variables for factors
            df_encoded = pd.get_dummies(
                df, columns=["Condition", "Timepoint"], drop_first=True
            )

            # Fit OLS model
            predictor_cols = [
                col
                for col in df_encoded.columns
                if col.startswith(("Condition_", "Timepoint_"))
            ]
            if predictor_cols:
                formula_parts = ["Value"] + ["~"] + [" + ".join(predictor_cols)]
                formula = "".join(formula_parts)

                model = ols(formula, data=df_encoded).fit()

                # Breusch-Pagan test
                lm, lm_pvalue, fvalue, f_pvalue = het_breuschpagan(
                    model.resid, model.model.exog
                )

                return {
                    "test": "Breusch-Pagan Test",
                    "statistic": lm,
                    "p_value": lm_pvalue,
                    "assumption_met": lm_pvalue > 0.05,
                    "interpretation": (
                        "Homoscedasticity assumed"
                        if lm_pvalue > 0.05
                        else "Heteroscedasticity detected"
                    ),
                }
        except Exception as e:
            print(f"Error in Breusch-Pagan test: {e}")

        return {
            "test": "Breusch-Pagan Test",
            "statistic": np.nan,
            "p_value": np.nan,
            "assumption_met": False,
            "interpretation": "Could not compute",
        }

    def run_anova(
        self,
        df: pd.DataFrame,
        anova_type: str = "factorial",
        factors: List[str] = None,
        include_interaction: bool = True,
    ) -> Dict[str, Any]:
        """
        Run ANOVA analysis

        Args:
            df: DataFrame with Value and factor columns
            anova_type: Type of ANOVA ('factorial', 'repeated', 'mixed')
            factors: List of factors to include
            include_interaction: Whether to include interaction terms

        Returns:
            Dictionary with ANOVA results
        """
        if factors is None:
            factors = ["Condition", "Timepoint"]

        try:
            # Prepare formula
            formula_parts = ["Value ~ "]

            if len(factors) == 1:
                formula_parts.append(factors[0])
            elif len(factors) == 2:
                formula_parts.append(factors[0])
                formula_parts.append(" + ")
                formula_parts.append(factors[1])
                if include_interaction:
                    formula_parts.append(" + ")
                    formula_parts.append(f"{factors[0]}:{factors[1]}")

            formula = "".join(formula_parts)

            # Fit model
            model = ols(formula, data=df).fit()

            # Run ANOVA
            anova_results = anova_lm(model, typ=2)

            # Calculate effect sizes (partial eta squared)
            anova_results["partial_eta_sq"] = anova_results["sum_sq"] / (
                anova_results["sum_sq"] + anova_results["sum_sq"].iloc[-1]
            )

            # Calculate observed power (simplified)
            anova_results["observed_power"] = (
                np.nan
            )  # Would need specialized calculation

            return {
                "model": model,
                "anova_table": anova_results,
                "formula": formula,
                "r_squared": model.rsquared,
                "adj_r_squared": model.rsquared_adj,
            }

        except Exception as e:
            print(f"Error in ANOVA: {e}")
            return {"error": str(e), "anova_table": None}

    def run_posthoc_test(
        self, df: pd.DataFrame, factor: str, test_type: str = "tukey"
    ) -> List[Dict[str, Any]]:
        """
        Run post-hoc tests

        Args:
            df: DataFrame with Value and factor columns
            factor: Factor to test ('Condition', 'Timepoint', or 'interaction')
            test_type: Type of test ('tukey', 'bonferroni')

        Returns:
            List of pairwise comparison results
        """
        results = []

        try:
            if factor == "interaction":
                # Create interaction groups
                df["interaction_group"] = (
                    df["Condition"].astype(str) + " × " + df["Timepoint"].astype(str)
                )
                factor_col = "interaction_group"
            else:
                factor_col = factor

            if test_type == "tukey":
                # Tukey HSD test
                mc = MultiComparison(df["Value"], df[factor_col])
                tukey_result = mc.tukeyhsd()

                # Parse results
                for i, row in enumerate(tukey_result.summary().data[1:]):  # Skip header
                    results.append(
                        {
                            "group1": row[0],
                            "group2": row[1],
                            "mean_diff": float(row[2]),
                            "std_error": float(row[3]) if len(row) > 3 else np.nan,
                            "p_value": float(row[4]) if len(row) > 4 else float(row[3]),
                            "significant": (
                                "Yes"
                                if float(row[4] if len(row) > 4 else row[3]) < 0.05
                                else "No"
                            ),
                        }
                    )

            elif test_type == "bonferroni":
                # Bonferroni correction with t-tests
                groups = df[factor_col].unique()
                n_comparisons = len(groups) * (len(groups) - 1) // 2
                alpha_corrected = 0.05 / n_comparisons

                for i, group1 in enumerate(groups):
                    for group2 in groups[i + 1 :]:
                        data1 = df[df[factor_col] == group1]["Value"]
                        data2 = df[df[factor_col] == group2]["Value"]

                        if len(data1) >= 2 and len(data2) >= 2:
                            t_stat, p_val = stats.ttest_ind(data1, data2)

                            results.append(
                                {
                                    "group1": group1,
                                    "group2": group2,
                                    "mean_diff": data1.mean() - data2.mean(),
                                    "std_error": np.sqrt(
                                        data1.var() / len(data1)
                                        + data2.var() / len(data2)
                                    ),
                                    "t_value": t_stat,
                                    "p_value": p_val,
                                    "p_corrected": p_val * n_comparisons,
                                    "significant": (
                                        "Yes" if p_val < alpha_corrected else "No"
                                    ),
                                }
                            )

        except Exception as e:
            print(f"Error in post-hoc test: {e}")
            results.append({"error": str(e)})

        return results

    def run_paired_tests(
        self,
        df: pd.DataFrame,
        test_type: str = "paired_t",
        group_factor: str = "Timepoint",
    ) -> List[Dict[str, Any]]:
        """
        Run paired t-test or Wilcoxon signed-rank test

        Args:
            df: DataFrame with Value column and grouping variables
            test_type: Type of test ('paired_t' or 'wilcoxon')
            group_factor: Factor to group by for pairing ('Timepoint' or 'Condition')

        Returns:
            List of test results dictionaries
        """
        results = []

        try:
            # Get unique values of the grouping factor
            groups = df[group_factor].unique()

            if len(groups) < 2:
                results.append(
                    {
                        "error": f"Need at least 2 groups in {group_factor} for paired testing"
                    }
                )
                return results

            # For paired tests, we need to match participants across groups
            pivot_df = df.pivot_table(
                values="Value",
                index="Participant",
                columns=group_factor,
                aggfunc="mean",
            )

            # Remove participants that don't have data for all groups
            complete_data = pivot_df.dropna()

            if len(complete_data) < 3:
                results.append(
                    {
                        "error": f"Need at least 3 participants with complete data for paired testing (found {len(complete_data)})"
                    }
                )
                return results

            # Perform pairwise comparisons between all groups
            for i, group1 in enumerate(groups):
                for group2 in groups[i + 1 :]:
                    if (
                        group1 in complete_data.columns
                        and group2 in complete_data.columns
                    ):
                        data1 = complete_data[group1].values
                        data2 = complete_data[group2].values

                        # Calculate descriptive statistics
                        mean1 = np.mean(data1)
                        mean2 = np.mean(data2)
                        std1 = np.std(data1, ddof=1)
                        std2 = np.std(data2, ddof=1)
                        diff = data1 - data2
                        mean_diff = np.mean(diff)
                        std_diff = np.std(diff, ddof=1)
                        se_diff = std_diff / np.sqrt(len(diff))

                        if test_type == "paired_t":
                            # Paired t-test
                            t_stat, p_value = stats.ttest_rel(data1, data2)

                            # Calculate 95% confidence interval for the difference
                            t_critical = stats.t.ppf(0.975, len(diff) - 1)
                            ci_lower = mean_diff - t_critical * se_diff
                            ci_upper = mean_diff + t_critical * se_diff

                            # Calculate Cohen's d for effect size
                            cohens_d = mean_diff / std_diff if std_diff > 0 else 0

                            results.append(
                                {
                                    "comparison": f"{group1} vs {group2}",
                                    "test_type": "Paired t-test",
                                    "n_pairs": len(diff),
                                    "mean_group1": mean1,
                                    "std_group1": std1,
                                    "mean_group2": mean2,
                                    "std_group2": std2,
                                    "mean_difference": mean_diff,
                                    "std_difference": std_diff,
                                    "se_difference": se_diff,
                                    "t_statistic": t_stat,
                                    "degrees_freedom": len(diff) - 1,
                                    "p_value": p_value,
                                    "ci_lower": ci_lower,
                                    "ci_upper": ci_upper,
                                    "cohens_d": cohens_d,
                                    "significant": "Yes" if p_value < 0.05 else "No",
                                    "effect_size": self._interpret_cohens_d(
                                        abs(cohens_d)
                                    ),
                                }
                            )

                        elif test_type == "wilcoxon":
                            # Wilcoxon signed-rank test
                            # Remove zero differences for Wilcoxon test
                            non_zero_diff = diff[diff != 0]

                            if len(non_zero_diff) < 3:
                                results.append(
                                    {
                                        "comparison": f"{group1} vs {group2}",
                                        "test_type": "Wilcoxon signed-rank test",
                                        "error": "Not enough non-zero differences for Wilcoxon test",
                                    }
                                )
                                continue

                            w_stat, p_value = stats.wilcoxon(data1, data2)

                            # Calculate effect size (r = Z / sqrt(N))
                            z_score = (
                                stats.norm.ppf(1 - p_value / 2) if p_value > 0 else 0
                            )
                            r_effect_size = abs(z_score) / np.sqrt(len(diff))

                            results.append(
                                {
                                    "comparison": f"{group1} vs {group2}",
                                    "test_type": "Wilcoxon signed-rank test",
                                    "n_pairs": len(diff),
                                    "n_non_zero": len(non_zero_diff),
                                    "mean_group1": mean1,
                                    "mean_group2": mean2,
                                    "median_group1": np.median(data1),
                                    "median_group2": np.median(data2),
                                    "mean_difference": mean_diff,
                                    "w_statistic": w_stat,
                                    "p_value": p_value,
                                    "z_score": z_score,
                                    "r_effect_size": r_effect_size,
                                    "significant": "Yes" if p_value < 0.05 else "No",
                                    "effect_size": self._interpret_r_effect_size(
                                        r_effect_size
                                    ),
                                }
                            )

        except Exception as e:
            print(f"Error in paired tests: {e}")
            results.append({"error": str(e)})

        return results

    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size"""
        if d < 0.2:
            return "Negligible"
        elif d < 0.5:
            return "Small"
        elif d < 0.8:
            return "Medium"
        else:
            return "Large"

    def _interpret_r_effect_size(self, r: float) -> str:
        """Interpret r effect size for Wilcoxon test"""
        if r < 0.1:
            return "Negligible"
        elif r < 0.3:
            return "Small"
        elif r < 0.5:
            return "Medium"
        else:
            return "Large"

    def get_available_variables(self, analyzer, metric_type: str) -> List[str]:
        """
        Get available variables for a given metric type

        Args:
            analyzer: GrangerCausalityAnalyzer instance
            metric_type: Type of metric ('Global', 'Nodal', 'Pairwise')

        Returns:
            List of available variable names
        """
        variables = set()

        if not analyzer.analyses:
            return []

        for analysis in analyzer.analyses.values():
            if metric_type == "Global" and "global" in analysis:
                variables.update(analysis["global"].keys())
            elif metric_type == "Nodal" and "nodal" in analysis:
                variables.update(analysis["nodal"].keys())
            elif metric_type == "Pairwise" and "pairwise" in analysis:
                variables.update(analysis["pairwise"].keys())

        return sorted(list(variables))


# Singleton instance for easy access
_statistics_service = None


def get_statistics_service() -> StatisticsService:
    """Get the singleton statistics service instance"""
    global _statistics_service
    if _statistics_service is None:
        _statistics_service = StatisticsService()
    return _statistics_service
