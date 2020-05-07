import pandas as pd
import matplotlib.pyplot as plt
import glob

class water_balance:
    """Annual water balance information of a PCR-GLOBWB run. Data is retrieved from the log-file of this run.

    Arguments:
        fo (str): path to log-file
    """

    def __init__(self, fo):
        """Initiates water balance object based on PCR-GLOBWB log-file.
        """

        self.pcr_log_file = fo

    def get_annual_values(self):
        """Get annual values for a range of water balance components by parsing the log-file.

        Returns:
            dataframe: dataframe containing annual values of water balance components
        """

        varData = {
                "year" : [],
                "precipitation" : [],
                "actualET": [],
                "runoff": [],
                "totalPotentialGrossDemand": [],
                "baseflow": [],
                "storage": [],}

        varNames = varData.keys()

        for fileName in glob.glob(self.pcr_log_file):
            try:
                f = open(fileName, "r")
                lines = f.readlines()
                f.close()
            except:
                lines = ""
            for line in lines:
                varFields = line.split(" ")
                if len(varFields) > 2:
                    if varFields[2] == "pcrglobwb" and len(varFields) == 9:
                        try:
                            year = int(varFields[-1][:4])
                        except:
                            if varFields[2] == "pcrglobwb" and len(varFields) == 16: 
                                year = int(varFields[11][:4])
                        if year not in varData["year"]: 
                            varData["year"].append(year)
                    if len(varFields) > 15:
                        if varFields[7] == "days" and varFields[8] == "1" and varFields[9] == "to":
                            for var in varNames:
                                if varFields[6] == var:
                                    varData[var].append(float(varFields[14]))
                    if len(varFields) > 14:
                        if varFields[6] == "days" and varFields[7] == "1" and varFields[8] == "to":
                            for var in varNames:
                                if varFields[5] == var:
                                    varData[var].append(float(varFields[13]))
                                
        self.df = pd.DataFrame.from_dict(varData, orient='columns')

        return self.df

    def bar_plot(self, **kwargs):
        """Creates a bar plot of water balance components per year. This adds to the regular plotting options with pandas dataframes.
        """

        xlabel = kwargs.get('xlabel', "m3")
        ylabel = kwargs.get('ylabel', None)
        figsize = kwargs.get('figsize', (20,10))
        fontsize = kwargs.get('fontsize', 13)

        ax = self.df.plot.bar(x='year', figsize=figsize)

        ax.set_ylabel(xlabel, fontsize=fontsize)
        ax.set_xlabel(ylabel, fontsize=fontsize)

        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.07),
                  fancybox=True, shadow=True, ncol=len(self.df.columns), fontsize=fontsize)