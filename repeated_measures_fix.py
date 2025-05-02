# Prepare for repeated measures ANOVA
within_factors = []
if include_timepoint:
    within_factors.append("Timepoint")
if include_condition:
    within_factors.append("Condition")

# Determine between-subjects factor
between_factor = None
if self.factor_group.get() and "Group" in df.columns:
    between_factor = "Group"

# Choose the appropriate analysis based on factors
if len(within_factors) == 2:  # Both Timepoint and Condition
    print(f"Running 2-way repeated measures ANOVA with {within_factors} as within factors")
    result = pg.rm_anova2(
        data=df,
        dv="Value",
        within=within_factors,
        subject="Participant",
        detailed=True
    )
elif len(within_factors) == 1:  # Single within factor
    if between_factor:  # Mixed design
        print(f"Running mixed ANOVA with {within_factors[0]} as within factor and {between_factor} as between factor")
        result = pg.mixed_anova(
            data=df,
            dv="Value",
            within=within_factors[0],
            between=between_factor,
            subject="Participant",
            detailed=True
        )
    else:  # Simple repeated measures
        print(f"Running repeated measures ANOVA with {within_factors[0]} as within factor")
        result = pg.rm_anova(
            data=df,
            dv="Value",
            within=within_factors[0],
            subject="Participant",
            detailed=True
        )
else:
    messagebox.showwarning("Invalid Selection", "Please select at least one within-subjects factor (Timepoint or Condition)")
    return 