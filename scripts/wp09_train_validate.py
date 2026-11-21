"""WP09 eğitim artefaktlarının salt okunur kapanış denetimi; fit yapmaz."""
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd

from wp09_train import ROOT, QA, MODEL, preserve, sha, write_json


def read(name):
    return json.loads((QA / name).read_text(encoding='utf-8'))


def check_manifest(manifest):
    for path, expected in manifest.items():
        assert sha(ROOT / path) == expected, path


def main():
    prior_count = preserve()
    prior = read('prior_outputs_sha256.json')
    models = read('model_artifact_manifest.json')
    check_manifest(read('input_manifest.json'))
    check_manifest(models)
    assert len(models) == 380
    expected_models = {p for p in prior if p.startswith('models/')} | set(models)
    actual_models = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'models').rglob('*') if p.is_file()}
    assert expected_models == actual_models
    fit = pd.read_csv(QA / 'model_fit_summary.csv')
    assert len(fit) == 190 and fit.status.eq('OK').all()
    assert fit.optimizer_steps.sum() == 10867 and fit.optimizer_steps.gt(0).all()
    assert fit.selected_state_L2_change.gt(0).all()
    no = fit.model.eq('G_noPPI')
    assert fit.loc[no, 'maximum_message_gradient_norm'].eq(0).all()
    assert fit.loc[no, 'maximum_train_message_input_norm'].eq(0).all()
    assert fit.loc[~no, 'maximum_message_gradient_norm'].gt(0).all()
    assert fit.groupby('context').size().eq(5).all()
    assert fit.groupby('context').initial_state_sha256.nunique().eq(1).all()
    for row in fit.itertuples():
        path = MODEL / (row.job_key + '.npz')
        metadata = json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
        assert metadata['approved_run_config_sha256'] == sha(QA / 'run_config.json')
        assert metadata['parameters_sha256'] == sha(path)
        h = hashlib.sha256()
        with np.load(path, allow_pickle=False) as data:
            for name in sorted(data.files):
                a = data[name]
                assert np.isfinite(a).all()
                h.update(name.encode()); h.update(str(a.dtype).encode())
                h.update(str(a.shape).encode()); h.update(a.tobytes())
        assert h.hexdigest() == row.selected_state_sha256 == metadata['selected_state_sha256']
    train = read('training_complete.json')
    assert (train['source_drugs'], train['source_PT'], train['source_positives']) == (62, 1061, 6416)
    commit = read('selection_complete_before_test_scoring.json')
    check_manifest(commit['selections'])
    score = read('scoring_complete.json')
    evaluation = read('evaluation_complete.json')
    assert score['selection_commit_sha256'] == evaluation['selection_commit_sha256'] == sha(QA / 'selection_complete_before_test_scoring.json')
    assert score['outer_decisions_sha256_unchanged'] == commit['outer_epoch_decisions_sha256'] == sha(QA / 'outer_fit_and_selection.json')
    assert score['model_manifest_sha256'] == sha(QA / 'model_artifact_manifest.json')
    assert score['predictions_sha256'] == evaluation['OOF_predictions_sha256'] == sha(QA / 'oof_predictions.csv')
    assert evaluation['no_prediction_ensemble'] and not evaluation['refit_or_retuning']
    assert not evaluation['WP10']
    assert pd.read_csv(QA / 'excluded_comparison_keys.csv').empty
    status = pd.read_csv(QA / 'prediction_status_all62.csv')
    assert len(status) == 620
    assert status.groupby(['protocol', 'model']).apply(lambda x: x.status.eq('SCORED').sum(), include_groups=False).eq(61).all()
    assert pd.read_csv(QA / 'bootstrap_validity.csv').valid_replicates.eq(1000).all()
    test_text = (QA / 'test_results.txt').read_text(encoding='utf-8')
    assert 'Ran 24 tests in 17.025s' in test_text and test_text.rstrip().endswith('OK')
    notebook_path = ROOT / 'notebooks/WP09_training_results.ipynb'
    notebook = nbformat.read(notebook_path, as_version=4)
    nbformat.validate(notebook)
    code = [c for c in notebook.cells if c.cell_type == 'code']
    assert [c.execution_count for c in code] == list(range(1, 11))
    png_count = 0
    for cell in code:
        for output in cell.outputs:
            assert output.output_type != 'error'
            assert not (output.output_type == 'stream' and output.name == 'stderr')
            png_count += int('image/png' in output.get('data', {}))
    assert png_count == 8
    figures = ROOT / 'reports/figures/WP09/training_v1'
    assert len(list(figures.glob('*.png'))) == 8
    html = (figures / 'per_drug_ablation_interactive.html').read_text(encoding='utf-8')
    assert 'Plotly.newPlot' in html and '<script src=' not in html
    environment = {'python': platform.python_version(), 'platform': platform.platform()}
    for package in ('numpy', 'pandas', 'torch', 'scikit-learn', 'scipy', 'matplotlib', 'plotly', 'nbformat'):
        environment[package] = importlib.metadata.version(package)
    write_json(QA / 'environment.json', environment)
    paths = list((ROOT / 'scripts').glob('wp09_train*.py')) + [ROOT / 'tests/test_wp09_training.py', notebook_path,
        ROOT / 'reports/WP09_TRAINING_RESULTS.md', ROOT / 'reports/WP09_TRAINING_MODEL_CARD.md', ROOT / 'run_status.md']
    write_json(QA / 'code_manifest.json', {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)})
    result = {'status': 'PASS', 'prior_files_unchanged': prior_count, 'new_model_files': len(models),
        'fits_OK': len(fit), 'optimizer_steps': int(fit.optimizer_steps.sum()), 'model_states_rehashed': len(fit),
        'trainer_tests': 24, 'notebook_executed_cells': len(code), 'notebook_PNGs': png_count,
        'static_PNGs_visually_reviewed': 8, 'interactive_HTML_self_contained': True, 'live_browser_tested': False,
        'matched_comparison_key_exclusions': 0, 'bootstrap_replicates': 1000, 'WP10_started': False,
        'atom_bond_GNN_present': False, 'validation_ran_training': False,
        'semantics': 'Observed-record ranking only; unknown not biological negative; conditional CI not external validation'}
    write_json(QA / 'artifact_validation.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
