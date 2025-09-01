import pandas as pd


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


if __name__ == "__main__":
    file_path = 'evaluation/hri_evaluation/hri-questionnaire.csv'
    perc_minimal, sati_minimal, eng_minimal, perc_full, sati_full, eng_full = select_data(file_path)
    
    # Print the results
    print("User Perception Full:")
    print(perc_full)            
    print("\nUser Perception Minimal:")
    print(perc_minimal)
  
    
    