import re
import matplotlib.pyplot as plt
from difflib import SequenceMatcher


# helper functions
def prepare_str(input_str, normalized=False, ignore_list=[]):
    """ Processes string for similarity comparisons , cleans special characters
        and extra whitespaces if normalized is True and removes the substrings
        which are in ignore_list)
    Args:
        input_str (str) : input string to be processed
        normalized (bool) : if True , method removes special characters and
                            extra whitespace from string,
                            and converts to lowercase
        ignore_list (list) : the substrings which need to be removed from the
                             input string
    Returns:
       str : returns processed string
    """
    for ignore_str in ignore_list:
        input_str = re.sub(r'{0}'.format(ignore_str), "", input_str,
                           flags=re.IGNORECASE)

    if normalized is True:
        input_str = input_str.strip().lower()
        # clean special chars and extra whitespace
        input_str = re.sub("\W", "", input_str).strip()

    return input_str


# class definition
class rdcleaner:
    def __init__(self, record=[], threshold=0.9, sim_mode='name'):
        self.input_record = record
        self.sim_threshold = threshold
        self.sim_mode = sim_mode
        self.sim_tolerance = 0.05
        self.sim_upper_tolerance = threshold + self.sim_tolerance
        self.sim_lower_tolerance = threshold - self.sim_tolerance

        print self

        from collections import defaultdict
        self.raw = defaultdict(list)
        self.raw_ct = defaultdict(int)
        self.clean = defaultdict(list)
        self.clean_ct = defaultdict(int)
        for index, row in record.iterrows():
            # vendorname: alt name, adr, city, phone, joindate
            name = prepare_str(row[1], True, [',', '\.'])
            self.raw[name] = [row[2], row[3], row[4], row[5], row[7], row[8]]
            self.raw_ct[name] += 1

    def __repr__(self):
        """
        Quick printout of some basic info about this instance
        """
        return ("** Cleaning Analysis Setup **\n" +
                "Start with %s records\n" % len(self.input_record) +
                "similarity threshold = %.2f\n" % self.sim_threshold +
                "similarity mode = " + self.sim_mode)


    def inspect(self, max=5):
        n = 0
        for key, value in self.raw.iteritems():
            print key, value
            n += 1
            if n >= 5:
                break

    def plot(self, record,title=''):
        import pandas as pd
        self.raw_df = pd.Series(record)
        fig, axarr = plt.subplots(nrows=1, ncols=1, figsize=(7, 7))
        axarr.hist(self.raw_df, 100, (0, 200))
        axarr.set_title(title)
        axarr.set_xscale('log')
        axarr.set_yscale('log')
        axarr.xaxis.set_tick_params(labelsize=20)
        axarr.yaxis.set_tick_params(labelsize=20)
        axarr.set_xlabel('Number of Similar Records', fontsize=20)
        axarr.set_ylabel('# of Entries', fontsize=20)

    def sim(self, a, b):
        # String sequence comparison
        m = SequenceMatcher(None, a, b)
        sim_score = m.ratio()

        # if want to use the full record information
        # average the join date sim score with the name sim score
        if (self.sim_mode == 'full_record'):
            joindate_a = self.raw[a][5]
            joindate_b = self.clean[b][5]
            if (joindate_a != '') & (joindate_b != ''):
                # sim_score_joindate = SequenceMatcher(None, joindate_a, joindate_b).ratio()
                sim_score_joindate = 1 if joindate_a == joindate_b else 0
                # if sim_score_joindate == 1:
                #     print 'joindate:', joindate_a, joindate_b, sim_score_joindate
                sim_score = (sim_score+sim_score_joindate)/2

        if sim_score > self.sim_threshold:
            if sim_score < self.sim_upper_tolerance:
                print 'Found similar - Close call!!! sim_score = ', sim_score
                print a, self.raw[a]
                print b, self.raw[b]
                print
            return True
        else:
            if sim_score > self.sim_lower_tolerance:
                print 'Not similar - Close call!!! sim_score = ', sim_score
                print a, self.raw[a]
                print b, self.raw[b]
                print
            return False

    def group_sim(self):
        print '\n======== Cleaning Starts! ========='
        for raw_key, raw_value in self.raw.iteritems():
            # first time just add to the cleaned dict
            if len(self.clean) == 0:
                self.clean[raw_key] = raw_value
                self.clean_ct[raw_key] += 1
            else:
                found_sim = False
                for clean_key, clean_value in self.clean.iteritems():
                    # skip the raw entry if found similar record
                    if self.sim(raw_key, clean_key):
                        #print 'not counting the sim entry: ', raw_key, clean_key
                        self.clean_ct[clean_key] += 1
                        found_sim = True
                        break
                # if rawkey is not similar to any of the cleaned keys
                # add it as a new entry to the clean dict
                if not found_sim:
                    self.clean[raw_key] = raw_value
                    self.clean_ct[raw_key] += 1

    def summarize(self):
        print '# of raw vendors', len(self.raw)
        print '# of cleaned vendors', len(self.clean)
        print 'cleaned away:'
        diff = set(self.raw.keys()) - set(self.clean.keys())
        print diff
