# Install and Load libraries
library(tidyverse)

# Read in your CSV file
metrics <- read.csv("/Users/mkd/github/HCMA_York/Model_Test_Output.csv")

# View the first few rows of the data
head(metrics)

# 4. Reshape the data from wide to long format, now including 'Epoch'
metrics_long <- pivot_longer(metrics,
                             cols = c(mAP, mAR),
                             names_to = "Metric",
                             values_to = "Value") %>%
                mutate(Epoch = rep(metrics$Epoch, each = 2)) # Repeat Epoch for each Metric (mAP, mAR)

# Add the 'Tool' column (from the 'Network' column)
metrics_long$Tool <- metrics$Network[rep(1:nrow(metrics), each = 2)]

# 5. Make the grouped bar plot, including 'Epoch' in the facet
ggplot(metrics_long, aes(x = Tool, y = Value, fill = Metric)) +
  geom_col(position = "dodge") +
  facet_wrap(~ Epoch) + # Add facet by Epoch
  labs(title = "mAP and mAR Scores by Tool and Epoch",
       x = "Tool",
       y = "Score") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1, size = 10)) + # Rotate and reduce size
  scale_x_discrete(labels = function(x) str_wrap(x, width = 10)) # Wrap long labels

# 6. Save the plot
ggsave("bar_plot_with_epochs_adjusted.png", width = 8, height = 6)

# 7. Save the reshaped data with Epochs included
write.csv(metrics_long, "metrics_long_with_epochs.csv", row.names = FALSE)




