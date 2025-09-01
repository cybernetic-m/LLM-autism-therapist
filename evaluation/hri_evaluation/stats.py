import pandas as pd
from scipy.stats import ttest_rel


def select_data(file_path):

    '''
    This function reads the CSV file containing the questionnaire results and separates the data into 'perc_data' (User Perception Data), 
    'sati_data' (User Satisfaction Data), and 'eng_data' (User Engagement Data) DataFrames of both Experiment 'Minimal' and 'Full'.
    Args:
        file_path (str): The path to the CSV file containing the questionnaire results.
    Returns:
        perc_minimal (pd.DataFrame): DataFrame containing User Perception Data of Experiment Minimal.
        sati_minimal (pd.DataFrame): DataFrame containing User Satisfaction Data of Experiment Minimal.
        eng_minimal (pd.DataFrame): DataFrame containing User Engagement Data of Experiment Minimal.
        perc_full (pd.DataFrame): DataFrame containing User Perception Data of Experiment Full.
        sati_full (pd.DataFrame): DataFrame containing User Satisfaction Data of Experiment Full.
        eng_full (pd.DataFrame): DataFrame containing User Engagement Data of Experiment Full.
    '''

    # Define a dictionary to rename long column names to shorter ones (q1 means question 1, etc.)
    abbreviations = {
    # Start of User Perception questions
    'Il robot dialoga come un reale terapista umano': 'q1',
    'Il robot sembra esprimere emozioni come noi umani': 'q2',
    'Il robot ha atteggiamenti che mi aspetterei da un reale terapista umano': 'q3',
    'Il robot assume comportamenti credibili, naturali e poco artificiali': 'q4',
    'Il robot risponde in maniera intelligente': 'q5',
     # Start of User Satisfaction questions    
    'Adam mi ha fatto sentire sempre a mio agio': 'q6',
    'Dialogare con Adam è molto intuitivo e semplice ': 'q7',
    "Interagire con un Robot terapista è stata un' esperienza piacevole": 'q8',
    "L'interazione con Adam mi ha dato un livello soddisfacente di supporto, paragonabile a un terapista umano": 'q9',
    'Raccomanderei Adam ad un amico come supporto ad un terapeuta umano o in contesti dove non fosse possibile avere un terapista umano': 'q10',
    # Start of User Engagement questions
    'Adam è stato sempre interessante durante la conversazione': 'q11',
    'Mi sono sentito completamente immerso durante la conversazione con Adam': 'q12',
    'Dialogherei di nuovo con Adam in futuro': 'q13',
    'Mi sono sentito molto connesso con il robot durante la conversazione': 'q14',
    'Sono stato attento durante tutta la conversazione con Adam': 'q15'  
    }

    
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Separate data in Full and Minimal experiments
    full_data = df[df.iloc[:,2] == 'Full']
    minimal_data = df[df.iloc[:,2] == 'Minimal']

    # Then I select only the columns with ID (column 1) and the scores (from 3 to 17)
    full_data = full_data.iloc[:, [1] + list(range(3, 18))]
    minimal_data = minimal_data.iloc[:, [1] + list(range(3, 18))]

    # Rename the columns using the abbreviations dictionary
    full_data = full_data.rename(columns=abbreviations)
    minimal_data = minimal_data.rename(columns=abbreviations)

    # Separate the data into three DataFrames based on the type of questions (for both Full and Minimal)
    perc_full = full_data[['ID', 'q1', 'q2', 'q3', 'q4', 'q5']]
    sati_full = full_data[['ID', 'q6', 'q7', 'q8', 'q9', 'q10']]
    eng_full = full_data[['ID', 'q11', 'q12', 'q13', 'q14', 'q15']]

    perc_minimal = minimal_data[['ID', 'q1', 'q2', 'q3', 'q4', 'q5']]
    sati_minimal = minimal_data[['ID', 'q6', 'q7', 'q8', 'q9', 'q10']]
    eng_minimal = minimal_data[['ID', 'q11', 'q12', 'q13', 'q14', 'q15']]

    return perc_minimal, sati_minimal, eng_minimal, perc_full, sati_full, eng_full

def questionnaire_stats(data1, data2):
    '''
    This function computes importants Questionnaire stastistics such as means, standard deviations and p-value 
    using a paired t-test between two sets of data. Firstly it computes the sum of each row (user) points for both dataframes.
    In particular in a set of data = [x1, x2, ..., xn] each xi is the sum of the scores of a user (row) for all the questions (columns), it
    return the mean and standard deviation of the sums and the p-value of the paired t-test between the two.

    Args:
        data1 (pd.DataFrame): The first set of data: a DataFrame where each row is a user and each column is a question score 
        data2 (pd.DataFrame): The second set of data: a DataFrame where each row is a user and each column is a question score 
    Returns:
        mean1 (float): The mean of the sums of first set of data.
        mean2 (float): The mean of the second set of data.
        std1 (float): The standard deviation of the first set of data.
        std2 (float): The standard deviation of the second set of data.
        p_value (float): The computed p-value from the paired t-test.
    '''

    #print("Data1:\n", data1)

    # Firstly we compute the sum of each row (user) points for both dataframes
    # :1 means that we want to select all the rows and all the columns except the first one (ID column)
    sum_df1 = data1.iloc[:, 1:].sum(axis=1)  
    sum_df2 = data2.iloc[:, 1:].sum(axis=1)  

    # Then we compute the mean of the sums
    mean1 = sum_df1.iloc[:].sum()/ (sum_df1.shape[0])  # Divide by the number of users (rows)
    mean2 = sum_df2.iloc[:].sum()/ (sum_df2.shape[0])

    # Compute the standard deviation of the sums
    std1 = sum_df1.std()
    std2 = sum_df2.std()

    # Perform a paired t-test (to perform that we pass the two arrays of sums)
    t_stat, p_value = ttest_rel(sum_df1, sum_df2)  

    return mean1, mean2, std1, std2, p_value


if __name__ == "__main__":
    file_path = 'evaluation/hri_evaluation/hri-questionnaire.csv'
    perc_minimal, sati_minimal, eng_minimal, perc_full, sati_full, eng_full = select_data(file_path)

    #print("User Perception Data Minimal:\n", perc_minimal)
    #print("\nUser Satisfaction Data Minimal:\n", sati_minimal)
    #print("\nUser Engagement Data Minimal:\n", eng_minimal)

    #print("\nUser Perception Data Full:\n", perc_full)
    #print("\nUser Satisfaction Data Full:\n", sati_full)
    #print("\nUser Engagement Data Full:\n", eng_full)
    
    # Initialize a dict to store the p-values
    stats_dict = {'User Perception': {'Mean Minimal': [], 'Mean Full': [], 'Std Minimal': [], 'Std Full': [], 'P Value': []}, 'User Satisfaction': {'Mean Minimal': [], 'Mean Full': [], 'Std Minimal': [], 'Std Full': [], 'P Value': []}, 'User Engagement': {'Mean Minimal': [], 'Mean Full': [], 'Std Minimal': [], 'Std Full': [], 'P Value': []}}

    # Perform paired t-tests
    for name, data_minimal, data_full in zip(
        ["User Perception", "User Satisfaction", "User Engagement"],
        [perc_minimal, sati_minimal, eng_minimal],
        [perc_full, sati_full, eng_full]
    ):
        # Compute statistics
        mean1, mean2, std1, std2, p = questionnaire_stats(data_minimal, data_full)

        # Append the stats to the dictionary
        stats_dict[name]['Mean Minimal'].append(mean1)
        stats_dict[name]['Mean Full'].append(mean2)
        stats_dict[name]['Std Minimal'].append(std1)
        stats_dict[name]['Std Full'].append(std2)
        stats_dict[name]['P Value'].append(p)

        # Print the results
        print(f"\n{name} Statistics:")
        print(f"Mean Minimal: {mean1:.2f}, Mean Full: {mean2:.2f}")
        print(f"Std Minimal: {std1:.2f}, Std Full: {std2:.2f}")
        print(f"P-value: {p:.4f}")

    # Save the p-values in a CSV file
    stats_df = pd.DataFrame(stats_dict)
    stats_df.to_csv('evaluation/hri_evaluation/stats.csv', index=False)
    print("\nStats saved to 'evaluation/hri_evaluation/stats.csv'")
  
    
    