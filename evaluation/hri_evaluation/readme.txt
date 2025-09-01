Inside this you can find:

1. 'hri-questionnaire.csv': it is a csv file summarizing the Godspeed Questionnaire that we have proposed to a group of 10 people. 
                            If you want to know the detail about that, I suggest you to read section 7.1 HRI Evaluation of "report.pdf"
                            We have conducted two types of experiments called 'minimal' and 'full', the study is about the difference between them.

2. 'stats.py': it is the python file that read the questionnaire and do the computation of the statistics, such as means, standard deviations 
                and p-value used to reject or not reject the null hypothesis. If you run the code you will produce the file 'stats.csv'

3. 'stats.csv': it is the csv file with all the statistics. In particular you can find something like: 
                
                User Perception,    User Satisfaction,     User Engagement
                [18.555555555555557],[21.333333333333332],[22.555555555555557]
                [19.88888888888889],[21.77777777777778],[22.77777777777778]
                [3.0046260628866577],[3.4641016151377544],[2.650995620097811]
                [4.166666666666667],[3.2317865716108862],[2.7284509239574835]
                [0.08051623795726257],[0.4027592281495932],[0.6223833291543435]

                in which per column you see ours dependent variables of the HRI study and per rows 
                the mean_minimal, mean_full, std_minimal, std_full, p_value respectively.


            