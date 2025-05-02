#!/usr/bin/env python

# Read the file
with open('src/gui.py', 'r') as f:
    content = f.read()

# Fix the rm_anova2 issue
replacement = '''                    # Choose the appropriate analysis based on factors
                    if len(within_factors) == 2:  # Both Timepoint and Condition
                        print(f"Running 2-way repeated measures ANOVA with {within_factors} as within factors")
                        try:
                            # Try using rm_anova2 if available in this version of Pingouin
                            result = pg.rm_anova2(
                                data=df,
                                dv="Value",
                                within=within_factors,
                                subject="Participant",
                                detailed=True
                            )
                        except AttributeError:
                            # Fall back to running repeated measures ANOVA for each factor separately
                            print("rm_anova2 not available in this version of Pingouin, running separate ANOVAs for each factor")
                            
                            # Create a list to store both results
                            result_list = []
                            
                            # Run ANOVA for first factor
                            result1 = pg.rm_anova(
                                data=df,
                                dv="Value",
                                within=within_factors[0],
                                subject="Participant",
                                detailed=True
                            )
                            result1['Source'] = result1['Source'].apply(lambda x: f"{within_factors[0]}: {x}" if x != 'Within' else x)
                            result_list.append(result1)
                            
                            # Run ANOVA for second factor
                            result2 = pg.rm_anova(
                                data=df,
                                dv="Value",
                                within=within_factors[1],
                                subject="Participant",
                                detailed=True
                            )
                            result2['Source'] = result2['Source'].apply(lambda x: f"{within_factors[1]}: {x}" if x != 'Within' else x)
                            result_list.append(result2)
                            
                            # Combine results (this is an approximation, not a true interaction test)
                            result = pd.concat(result_list)'''

# Replace the problematic code
content = content.replace('''                    # Choose the appropriate analysis based on factors
                    if len(within_factors) == 2:  # Both Timepoint and Condition
                        print(f"Running 2-way repeated measures ANOVA with {within_factors} as within factors")
                        result = pg.rm_anova2(
                            data=df,
                            dv="Value",
                            within=within_factors,
                            subject="Participant",
                            detailed=True
                        )''', replacement)

# Write the file back
with open('src/gui.py', 'w') as f:
    f.write(content)

print("Fixed rm_anova2 issue") 