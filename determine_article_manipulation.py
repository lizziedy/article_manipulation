import masters_project_helper as mph
import analysis.document_statistics as ds
import analysis.baseline as bl

def do_baseline_analysis():
    bl.get_baselines()
    ds.add_sentiments()
    ds.add_manipulation()

if __name__ == '__main__':
    do_baseline_analysis()
